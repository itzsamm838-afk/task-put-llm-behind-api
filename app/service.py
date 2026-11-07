import os
import json
import logging
from pathlib import Path
from pydantic import ValidationError
from app.schemas import StudyExtraction
from app.llm import call_model, PROMPT_VERSION

logger = logging.getLogger("a17.service")
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "study-extractor-v1.md"
QUARANTINE_PATH = Path(__file__).resolve().parent.parent / "logs" / "quarantine.jsonl"

def _stub():
    return StudyExtraction(
        task="emotion_recognition",
        architecture_family="transformer",
        dataset="DEAP",
        evaluation_metrics=["accuracy"],
        reported_performance="Not stated in supplied text",
        evidence_summary="Stub response for local development; not extracted from a paper.",
        confidence=0.0,
        needs_review=True,
    )

def _load_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")

def _parse_validate(raw: str) -> StudyExtraction:
    # Permit a fenced JSON response, but never return raw model text.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("No JSON object found")
    data = json.loads(cleaned[start:end + 1])
    return StudyExtraction.model_validate(data)

def _quarantine(text, raw, error):
    QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "prompt_version": PROMPT_VERSION,
        "input": text,
        "raw_output": raw,
        "error": str(error),
    }
    with QUARANTINE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\\n")

def extract_study(text: str) -> StudyExtraction:
    if os.getenv("LLM_STUB", "0") == "1":
        return _stub()
    prompt = _load_prompt()
    raw, _ = call_model(prompt, json.dumps({"paper_text": text}, ensure_ascii=False))
    try:
        return _parse_validate(raw)
    except (ValueError, json.JSONDecodeError, ValidationError) as first_error:
        repair_user = (
            "INPUT: " + json.dumps({"paper_text": text}, ensure_ascii=False) +
            "\\nPREVIOUS INVALID OUTPUT: " + raw +
            "\\nVALIDATION ERROR: " + str(first_error) +
            "\\nYour previous answer was rejected. Return only corrected JSON matching the schema."
        )
        repaired_raw, _ = call_model(prompt, repair_user, repaired=True)
        try:
            return _parse_validate(repaired_raw)
        except (ValueError, json.JSONDecodeError, ValidationError) as second_error:
            _quarantine(text, repaired_raw, second_error)
            raise ValueError("Model output remained invalid after one repair") from second_error
