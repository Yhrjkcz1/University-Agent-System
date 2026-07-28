"""
Diagnostic: Run the current ReAgent_New scoring on the sample data
to demonstrate irrelevant competition scoring behavior.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.ReAgent_New import RecommendationAgent
from agents.ReAgent_New.utils import load_config
from agents.ReAgent_New.weights import normalize_weights
from datetime import date

# Load config
config = load_config()
rec_cfg = dict(config.get("recommendation") or {})
copy_cfg = dict(rec_cfg.get("llm_copywriting") or {})
copy_cfg["enabled"] = False
rec_cfg["llm_copywriting"] = copy_cfg
rerank_cfg = dict(rec_cfg.get("semantic_rerank") or {})
rerank_cfg["enabled"] = False
rec_cfg["semantic_rerank"] = rerank_cfg
rec_cfg["quality_gate"] = {"enabled": False}
rec_cfg["prestige"] = {"enabled": False}
rec_cfg["diversity"] = {"enabled": False}
config["recommendation"] = rec_cfg

agent = RecommendationAgent(config)

# Load sample
sample_path = ROOT / "tests" / "fixtures" / "recommendation_input_sample.json"
payload = json.loads(sample_path.read_text(encoding="utf-8"))

# Run
result = agent.run(payload)

print("=" * 100)
print(f"USER: {payload['user_profile']['major']} 专业, "
      f"interests={payload['user_profile']['interests']}, "
      f"skills={payload['user_profile']['skills']}")
print(f"目标: AI相关竞赛")
print("=" * 100)

# Print all scored items from recommendation_pool
pool = result["data"].get("recommendation_pool", result["data"].get("recommendations", []))
print(f"\n推荐池共 {len(pool)} 个项目\n")

print(f"{'排名':>4}  {'竞赛名称':<40} {'综合分':>6} {'等级':>3}  {'专业':>5} {'年级':>5} {'兴趣':>5} {'能力':>5} {'截止':>5} {'团队':>5}  {'推荐理由'}")
print("-" * 120)

for i, rec in enumerate(pool):
    detail = rec["scores"] if "scores" in rec else rec.get("detail", {})
    level = rec.get("recommend_level", rec.get("level", "?"))
    reason = rec.get("reason", "")
    title = rec.get("title", rec.get("item", {}).get("title", "?"))
    print(f"{i+1:>4}  {title:<40} {rec['total']:>6.1f} {level:>3}  "
          f"{detail.get('major_score', 0):>5.0f} "
          f"{detail.get('grade_score', 0):>5.0f} "
          f"{detail.get('interest_score', 0):>5.0f} "
          f"{detail.get('ability_score', 0):>5.0f} "
          f"{detail.get('deadline_score', 0):>5.0f} "
          f"{detail.get('team_score', 0):>5.0f}  "
          f"{reason[:50]}")

print(f"\n\n=== 详细维度分析（按兴趣分降序排列）===")
print(f"{'竞赛名称':<40} {'专业':>5} {'年级':>5} {'兴趣':>5} {'能力':>5} {'截止':>5} {'团队':>5} | {'综合':>6} | {'tags':<30} {'category':<10}")
print("-" * 140)

# Sort by interest score descending
pool_sorted = sorted(pool, key=lambda r: r["scores"].get("interest_score", 0), reverse=True)
for rec in pool_sorted:
    detail = rec["scores"]
    item = rec.get("item", {})
    reqs = item.get("requirements", {})
    tags = str(reqs.get("tags", []))
    cat = str(reqs.get("category", ""))
    title = item.get("title", "?")
    print(f"{title:<40} "
          f"{detail.get('major_score', 0):>5.0f} "
          f"{detail.get('grade_score', 0):>5.0f} "
          f"{detail.get('interest_score', 0):>5.0f} "
          f"{detail.get('ability_score', 0):>5.0f} "
          f"{detail.get('deadline_score', 0):>5.0f} "
          f"{detail.get('team_score', 0):>5.0f} | "
          f"{rec['total']:>6.1f} | "
          f"{tags[:30]:<30} {cat:<10}")

print(f"\n\n=== AI相关竞赛兴趣分分析 ===")
print("用户兴趣: ['人工智能', '算法竞赛', '数学建模']")
print("---")
ai_related_tags = ["人工智能", "AI", "算法", "编程", "计算机"]
for rec in pool:
    item = rec.get("item", {})
    reqs = item.get("requirements", {})
    tags = [str(t).lower() for t in (reqs.get("tags", []) or [])]
    category = (reqs.get("category", "") or "").lower()
    title = item.get("title", "?")
    interest = rec["scores"].get("interest_score", 0)
    
    # Check if this should be AI-related
    has_ai = any(t in ai_tags for ai_tags in [["人工智能", "ai"], ["算法", "算法编程", "算法竞赛"], ["编程", "计算机"]]
                 for t in tags if t in ai_tags or any(kw in t for kw in ["人工智能", "ai", "算法", "编程", "计算机"]))
    
    # Simpler check
    is_ai_related = any(word in str(tags+[category]) for word in ["人工智能", "ai", "算法", "编程", "计算机", "博弈", "统计科学"])

    marker = " [AI/CS] " if is_ai_related else " [NON-AI]"
    print(f"{interest:>5.0f}分 {marker} {title:<45} tags={str(tags[:4]):<40} cat={category:<15}")

print("\n")
print("=" * 100)
print("KEY OBSERVATIONS:")
print("=" * 100)

# 1. Check if English competitions appear in top 3
recs = result["data"].get("recommendations", pool)
top3 = [r.get("title", r.get("item", {}).get("title", "?")) for r in recs[:3]]
print(f"\nTop-3 推荐: {top3}")
english_in_top = [t for t in top3 if any(kw in t for kw in ["英语", "翻译", "阅读", "外交"])]
if english_in_top:
    print(f"⚠️  问题: 英语类竞赛出现在 Top-3: {english_in_top}")
else:
    print(f"✓  Top-3 无不相关英语竞赛")

# 2. Check interest scores for AI vs English comps
ai_comps = []
eng_comps = []
for rec in pool:
    item = rec.get("item", {})
    reqs = item.get("requirements", {})
    tags = str([str(t).lower() for t in (reqs.get("tags", []) or [])])
    title = item.get("title", "?")
    interest = rec["scores"].get("interest_score", 0)
    if any(w in tags for w in ["人工智能", "ai", "算法编程", "计算机"]):
        ai_comps.append((title, interest))
    if any(w in str(tags).lower() for w in ["英语", "翻译", "外语"]):
        eng_comps.append((title, interest))

print(f"\nAI/CS 类竞赛兴趣分: {ai_comps}")
print(f"英语类竞赛兴趣分:  {eng_comps}")

# 3. Check major scores (should be 90 for comps without target_majors)
for rec in pool:
    item = rec.get("item", {})
    title = item.get("title", "?")
    major_score = rec["scores"].get("major_score", 0)
    if major_score < 90:
        print(f"⚠️  专业分非90: {title:<50} 专业分={major_score}")
