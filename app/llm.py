import os
import json
import time
import random
import logging
from openai import OpenAI, APIStatusError, APITimeoutError, APIConnectionError

logger = logging.getLogger("a17.llm")
PROMPT_VERSION = "study-extractor-v1"

def _client():
    return OpenAI(
        base_url=os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1"),
        api_key=os.getenv("LLM_API_KEY", ""),
        timeout=30.0,
        max_retries=0,  # SDK retries disabled; retry policy is explicit below.
    )

def _log_usage(response, duration_ms, repaired):
    usage = getattr(response, "usage", None)
    logger.info(json.dumps({
        "event": "llm_call",
        "prompt_version": PROMPT_VERSION,
        "model": os.getenv("LLM_MODEL", "openrouter/free"),
        "input_tokens": getattr(usage, "prompt_tokens", None) if usage else None,
        "output_tokens": getattr(usage, "completion_tokens", None) if usage else None,
        "duration_ms": duration_ms,
        "repair": repaired,
    }))

def call_model(system_prompt: str, user_content: str, repaired: bool = False):
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        raise RuntimeError("LLM_DISABLED")
    client = _client()
    last_error = None
    for attempt, delay in enumerate((0, 1, 2), start=1):
        started = time.monotonic()
        try:
            response = client.chat.completions.create(
                model=os.getenv("LLM_MODEL", "openrouter/free"),
                temperature=0.1,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
            _log_usage(response, int((time.monotonic() - started) * 1000), repaired)
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty model response")
            return content, response
        except APITimeoutError as exc:
            last_error = exc
        except APIConnectionError as exc:
            last_error = exc
        except APIStatusError as exc:
            status = exc.status_code
            if status not in (429, 500, 502, 503, 504):
                # In particular, never retry 400, 401, or 403.
                raise RuntimeError("MODEL_UNAVAILABLE") from exc
            last_error = exc
            retry_after = None
            try:
                retry_after = float(exc.response.headers.get("retry-after"))
            except (TypeError, ValueError, AttributeError):
                pass
            if attempt < 3:
                wait = retry_after if retry_after is not None else delay + random.uniform(0, 0.25)
                time.sleep(wait)
                continue
        if attempt < 3:
            time.sleep(delay + random.uniform(0, 0.25))
    if isinstance(last_error, APITimeoutError):
        raise TimeoutError from last_error
    raise RuntimeError("MODEL_UNAVAILABLE") from last_error
