"""检查推荐质量：数据、profile 提取、推荐逻辑"""
import json, sys

# --- 1. 检查竞赛数据 ---
with open('data/raw/competitions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
comps = data if isinstance(data, list) else data.get('competitions', [])

print(f"=== 竞赛数据总览：{len(comps)} 条 ===")
no_req = 0
for c in comps:
    reqs = c.get('requirements')
    if not reqs or not isinstance(reqs, dict):
        no_req += 1

print(f"  有 requirements 字段: {len(comps)-no_req}")
print(f"  无 requirements 字段: {no_req}")

# 查看所有竞赛的 category 分布
from collections import Counter
cats = Counter()
majors_set = set()
tags_set = set()
skills_set = set()
grades_set = set()

for c in comps:
    reqs = c.get('requirements') or {}
    if not isinstance(reqs, dict):
        reqs = {}
    cats[reqs.get('category', 'MISSING')] += 1
    for m in reqs.get('target_majors', []):
        majors_set.add(m)
    for t in reqs.get('tags', []):
        tags_set.add(t)
    for s in reqs.get('required_skills', []):
        skills_set.add(s)
    for g in reqs.get('target_grades', []):
        grades_set.add(g)

print(f"\ncategory 分布: {dict(cats)}")
print(f"target_majors 值: {sorted(majors_set)}")
print(f"tags 值: {sorted(tags_set)}")
print(f"required_skills 值: {sorted(skills_set)}")
print(f"target_grades 值: {sorted(grades_set)}")

# --- 3. 模拟用户输入 → profile 提取 ---
# 检查 info_extract_agent.py 逻辑
print("\n\n=== 检查 info_extract_agent 输出 ===")

# 模拟测试：向 API 发请求并查看 user_profile 的结构
import urllib.request, time

body = {
    'user_input': '我是计算机专业大二学生，推荐AI竞赛',
    'task_type': 'full_process',
    'user_profile': {},
    'context': {},
    'input_data': {},
    'history': [],
}
req = urllib.request.Request(
    'http://localhost:8000/api/agent/run',
    data=json.dumps(body).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
)
time.sleep(2)
try:
    resp = urllib.request.urlopen(req, timeout=120)
    data = json.loads(resp.read().decode('utf-8'))
    resp_data = data.get('response', {})
    print(f"Success: {data.get('success')}")
    print(f"Type: {resp_data.get('type')}")
    
    # 打印 user_profile
    up = resp_data.get('user_profile', {})
    print(f"\nuser_profile:")
    for k, v in up.items():
        print(f"  {k}: {v}")
    
    # 打印 recommendations
    recs = resp_data.get('recommendations', [])
    print(f"\nrecommendations count: {len(recs)}")
    for r in recs:
        print(f"  - {r.get('title')} | score={r.get('match_score')} | level={r.get('recommend_level')}")
        print(f"    major_score={r.get('detail',{}).get('major_score')} interest={r.get('detail',{}).get('interest_score')} ability={r.get('detail',{}).get('ability_score')}")
        print(f"    category={r.get('category_key')}")
except Exception as e:
    print(f"Error: {e}")
