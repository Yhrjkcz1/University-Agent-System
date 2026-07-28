"""Test the API endpoint to simulate frontend requests."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
import httpx

# Test 1: With full profile (simulating what the frontend sends)
print("=" * 60)
print("TEST 1: With profile (major + grade)")
print("=" * 60)
resp = httpx.post('http://localhost:8000/api/agent/run', json={
    'user_input': '我是计算机专业大二学生，推荐AI竞赛',
    'task_type': 'recommendation',
    'user_profile': {'major': '计算机科学与技术', 'grade': '大二'},
    'context': {},
    'input_data': {},
    'history': [],
}, timeout=120)

data = resp.json()
print('Success:', data.get('success'))
resp_data = data.get('response', {})
print('Type:', resp_data.get('type'))
print('Text:', resp_data.get('text','')[:200])
recs = resp_data.get('recommendations', [])
print('Recs count:', len(recs))

# Test 2: Without profile (like a new user)
print("\n" + "=" * 60)
print("TEST 2: Without profile (new user)")
print("=" * 60)
resp2 = httpx.post('http://localhost:8000/api/agent/run', json={
    'user_input': '推荐竞赛',
    'task_type': 'recommendation',
    'user_profile': {},
    'context': {},
    'input_data': {},
    'history': [],
}, timeout=120)

data2 = resp2.json()
print('Success:', data2.get('success'))
resp_data2 = data2.get('response', {})
print('Type:', resp_data2.get('type'))
print('Text:', resp_data2.get('text','')[:200])
recs2 = resp_data2.get('recommendations', [])
print('Recs count:', len(recs2))
