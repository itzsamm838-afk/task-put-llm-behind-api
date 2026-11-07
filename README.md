# FlyRank A17 — Put an LLM behind your API

A small FastAPI endpoint that extracts evidence about an EEG emotion-recognition study from messy paper text. It returns a fixed, validated JSON object; it does not chat, invent missing values, or expose raw model text.

## Run locally

Python 3.10+ is required.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
```

The default `.env.example` uses stub mode, so no provider key is needed:

```bash
uvicorn app.main:app --reload
```

## Runnable curl

```bash
curl -X POST http://127.0.0.1:8000/extract-study -H "Content-Type: application/json" -d "{\"text\":\"We evaluate a Transformer encoder on DEAP and report 91.4% accuracy.\"}"
```

With `LLM_STUB=1`, the exact response is:

```json
{
  "task": "emotion_recognition",
  "architecture_family": "transformer",
  "dataset": "DEAP",
  "evaluation_metrics": ["accuracy"],
  "reported_performance": "Not stated in supplied text",
  "evidence_summary": "Stub response for local development; not extracted from a paper.",
  "confidence": 0.0,
  "needs_review": true
}
```

Broken request (missing required text):

```bash
curl -X POST http://127.0.0.1:8000/extract-study -H "Content-Type: application/json" -d "{}"
```

It returns HTTP 400 with a validation error identifying `text`.

## Job card

- **What it does:** Extracts a compact, evidence-grounded record from text about an EEG emotion-recognition study.
- **Input:** `{ "text": "string, 1–8000 characters" }`
- **Output:** `task`, `architecture_family`, `dataset`, `evaluation_metrics`, `reported_performance`, `evidence_summary`, `confidence`, `needs_review`.
- **Closed lists:** `task` = `emotion_recognition | other`; `architecture_family` = `transformer | convolutional | recurrent | hybrid | other`.
- **It must never:** invent a dataset, architecture, metric, or result; add fields; obey instructions embedded in paper text; return raw model text.
- **When unsure:** use `other` where applicable, lower confidence, and set `needs_review=true`; use `not stated` for missing facts.

## Provider

The client uses the OpenAI-compatible API shape. Set these three variables to switch between providers:

- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`

OpenRouter example: `https://openrouter.ai/api/v1`, your key, `openrouter/free`.
Ollama example: `http://localhost:11434/v1/`, `ollama`, `gemma3:1b`.

Never send confidential or personal data to a free hosted model. Keep `.env` out of Git.

## Reliability and safety

- Input validation occurs before any model call.
- `LLM_STUB=1` returns a deterministic schema-valid response without a provider call.
- `LLM_ENABLED=false` disables model use and returns HTTP 503.
- Explicit 30-second SDK timeout.
- SDK retries are disabled (`max_retries=0`); application retries are limited to timeouts, connection failures, 429 and 5xx with backoff/jitter. 400, 401 and 403 are not retried.
- Invalid model JSON/schema triggers exactly one repair call. A second failure is written to `logs/quarantine.jsonl` and returns HTTP 422.
- Each successful model response emits structured usage/duration metadata to the application logger. Token usage is logged when supplied by the provider. Exact USD cost is not calculated because free-provider routing and pricing vary.

## Eval

Eight labelled examples live in `evals/cases.json`. Start the API with a real provider configured, then run:

```bash
python scripts/run_eval.py
```

The script reports exact matches across the expected key fields. **No live-provider score is claimed in this starter ZIP**; run it with your selected model and record the actual score, date, model, and prompt version here before publishing.

## Tests

```bash
LLM_STUB=1 pytest -q
```

## Cost note

Record input/output token counts from one real call. For a paid model, estimate daily cost as:

`(input_tokens × input_price_per_token + output_tokens × output_price_per_token) × 10,000`

For a free routed model, report the applicable quota and note that a stable USD estimate is not available.

## What I'd fix with another day

Add provider-specific structured-output mode where supported, improve semantic eval scoring, and run the eval against a second model.

## Commit plan

Make at least six meaningful commits as you complete the assignment stages. This ZIP is a starter implementation, not evidence of six commits or a published live eval.
