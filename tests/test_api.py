from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json() == {"status": "ok"}

def test_stub_returns_schema():
    import os
    os.environ["LLM_STUB"] = "1"
    response = client.post("/extract-study", json={"text": "A transformer on DEAP."})
    assert response.status_code == 200
    data = response.json()
    assert data["architecture_family"] == "transformer"
    assert set(data) == {
        "task", "architecture_family", "dataset", "evaluation_metrics",
        "reported_performance", "evidence_summary", "confidence", "needs_review"
    }

def test_invalid_input_rejected_before_model():
    response = client.post("/extract-study", json={"text": ""})
    assert response.status_code == 400
    assert "text" in response.text

def test_wrong_type_rejected():
    response = client.post("/extract-study", json={"text": 123})
    assert response.status_code == 422
