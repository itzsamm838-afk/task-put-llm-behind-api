import json
import os
import urllib.request
from pathlib import Path

BASE = os.getenv("API_URL", "http://127.0.0.1:8000")
cases = json.loads((Path(__file__).resolve().parents[1] / "evals" / "cases.json").read_text())
correct = 0
failures = []
for case in cases:
    body = json.dumps({"text": case["input"]}).encode()
    req = urllib.request.Request(BASE + "/extract-study", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            actual = json.loads(response.read())
        expected = case["expected"]
        matched = all(actual.get(k) == v for k, v in expected.items())
    except Exception as exc:
        matched = False
        actual = {"error": str(exc)}
    correct += int(matched)
    if not matched:
        failures.append({"id": case["id"], "expected": case["expected"], "actual": actual})
print(f"Key-field exact-match score: {correct}/{len(cases)} ({correct/len(cases)*100:.1f}%)")
print("Failures:", json.dumps(failures, indent=2))
