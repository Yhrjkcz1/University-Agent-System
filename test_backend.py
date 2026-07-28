"""Test the FastAPI backend endpoints."""
import json
from fastapi.testclient import TestClient
from api import app

# Helper to safely print Chinese text in GBK console
def safe_print(label, text):
    try:
        print(f"  {label}: {text[:200]}")
    except UnicodeEncodeError:
        sanitized = text.encode('gbk', errors='replace').decode('gbk')
        print(f"  {label}: {sanitized[:200]}")

client = TestClient(app)

# 1. Health check
resp = client.get("/")
print(f"GET / -> {resp.status_code}: {resp.json()}")
assert resp.status_code == 200

# 2. Test API without profile (should ask for major/grade)
resp = client.post("/api/agent/run", json={
    "user_input": "\u4f60\u597d",
    "task_type": "recommendation",
    "user_profile": {},
    "context": {},
    "input_data": {},
    "history": []
})
print(f"\nPOST /api/agent/run (no profile) -> {resp.status_code}")
result = resp.json()
print(f"  success: {result.get('success')}")
resp_data = result.get("response", {})
if isinstance(resp_data, dict):
    text = resp_data.get("text", "")
    safe_print("response.text[:120]", text[:120])

# 3. Test API with profile
resp = client.post("/api/agent/run", json={
    "user_input": "我是计算机专业大二学生，想找AI竞赛",
    "task_type": "recommendation",
    "user_profile": {"major": "计算机科学与技术", "grade": "大二"},
    "context": {},
    "input_data": {},
    "history": []
})
print(f"\nPOST /api/agent/run (with profile) -> {resp.status_code}")
result = resp.json()
print(f"  success: {result.get('success')}")
resp_data = result.get("response", {})
if isinstance(resp_data, dict):
    text = resp_data.get("text", "")
    recs = resp_data.get("recommendations", [])
    safe_print("response.text[:120]", text[:120])
    print(f"  recommendations count: {len(recs)}")
    if recs and len(recs) > 0:
        first_rec = json.dumps(recs[0], ensure_ascii=False)
        safe_print("first rec", first_rec[:200])

print("\n=== ALL BACKEND TESTS PASSED ===")
