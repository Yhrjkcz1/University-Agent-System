"""检查数据结构和recommendation agent 的数据流"""
import json, os

# 1. Check competitions data structure
with open('data/raw/competitions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
comps = data if isinstance(data, list) else data.get('competitions', [])

print(f"=== Competitions: {len(comps)} items ===")

# Count fields
fields_count = {}
for c in comps:
    for k in c:
        fields_count[k] = fields_count.get(k, 0) + 1
print(f"Field distribution: {dict(sorted(fields_count.items()))}")

# Check requirements field
has_reqs = [c for c in comps if c.get('requirements')]
print(f"\nComps with requirements field: {len(has_reqs)}")

if has_reqs:
    for c in has_reqs[:5]:
        reqs = c['requirements']
        print(f"{c['title'][:40]}...")
        print(f"  requirements type: {type(reqs).__name__}")
        if isinstance(reqs, dict):
            print(f"  target_majors: {reqs.get('target_majors', [])}")
            print(f"  tags: {reqs.get('tags', [])}")
            print(f"  category: {reqs.get('category')}")
            print(f"  target_grades: {reqs.get('target_grades', [])}")
            print(f"  required_skills: {reqs.get('required_skills', [])}")
        elif isinstance(reqs, list):
            print(f"  (list) {reqs}")
else:
    # No requirements - this is the raw data
    print("No structured requirements found!")
    print("\nSample items:")
    for c in comps[:3]:
        print(f"  {json.dumps(c, ensure_ascii=False)[:300]}")

# Check if there's a structured/storage version
storage_dir = os.path.join('data', 'storage')
if os.path.isdir(storage_dir):
    print(f"\n=== Storage dir contents ===")
    for root, dirs, files in os.walk(storage_dir):
        for f in files:
            print(f"  {os.path.join(root, f)}")

# Check ReAgent_New data directory
reagent_data = os.path.join('agents', 'ReAgent_New', 'data')
if os.path.isdir(reagent_data):
    print(f"\n=== ReAgent_New data ===")
    for root, dirs, files in os.walk(reagent_data):
        for f in files:
            print(f"  {os.path.join(root, f)}")
