from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.schemas import ExtractRequest, StudyExtraction
from app.service import extract_study

app = FastAPI(title="FlyRank A17 — Research Study Extractor", version="1.0.0")

@app.exception_handler(RequestValidationError)
async def request_validation_handler(request, exc):
    errors = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error.get("loc", ()) if part != "body") or "request"
        errors.append({"field": field, "message": error.get("msg", "Invalid value")})
    return JSONResponse(status_code=400, content={"error": "Invalid request", "fields": errors})

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/extract-study", response_model=StudyExtraction)
def extract_study_endpoint(payload: ExtractRequest):
    try:
        result = extract_study(payload.text)
        return result
    except TimeoutError:
        raise HTTPException(status_code=504, detail="The language model timed out.")
    except RuntimeError as exc:
        message = str(exc)
        if message == "LLM_DISABLED":
            raise HTTPException(status_code=503, detail="LLM feature is currently disabled.")
        if message == "MODEL_UNAVAILABLE":
            raise HTTPException(status_code=502, detail="The model provider is unavailable.")
        raise HTTPException(status_code=502, detail="The model request failed.")
    except ValueError:
        raise HTTPException(status_code=422, detail="The model could not produce valid study-extraction JSON.")
