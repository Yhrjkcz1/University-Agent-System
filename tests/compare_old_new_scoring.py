"""
对比旧版 (legacy) 和新版 (ReAgent_New) 的兴趣评分差异。
"""
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.recommendation_agent_legacy import RecommendationAgent as LegacyAgent
from agents.ReAgent_New import RecommendationAgent as NewAgent
from agents.ReAgent_New.utils import load_config, build_sample_input
from agents.ReAgent_New.scoring import score_interest
from agents.ReAgent_New.synonyms import conceptual_overlap_detail

# 加载
config = load_config()
legacy = LegacyAgent(config)
new_agent = NewAgent(config)
payload = build_sample_input(config)
structured = payload["input_data"]["structured_items"]
user = payload["user_profile"]
interest_tags = user.get("interests", [])

print("=" * 120)
print(f"用户兴趣: {interest_tags}")
print(f"竞赛总数: {len(structured)}")
print("=" * 120)

header = f"{'竞赛名称':<30} {'旧版兴趣分':>9} {'新版兴趣分':>9} {'旧版综合分':>9} {'新版综合分':>9}  tags"
print(header)
print("-" * 120)

for item in structured:
    title = (item.get("title") or "?")[:28]
    reqs = item.get("requirements", {})
    tags = list(reqs.get("tags", []) or [])
    cat = (reqs.get("category", "") or "").strip()
    all_tags = tags + ([cat] if cat and cat.lower() not in ("unknown", "学科竞赛", "其他") else [])

    # 旧版
    legacy_interest = legacy._score_interest(user, item)
    # 新版
    new_interest, signals = score_interest(user, item, new_agent.synonym_groups)

    # 为方便对比，使用相同权重计算综合分中的兴趣部分
    w = 0.30  # 兴趣权重
    legacy_weighted = legacy_interest * w
    new_weighted = new_interest * w

    tags_str = str(tags[:5])[:28]
    print(f"{title:<30} {legacy_interest:>9.1f} {new_interest:>9.1f} {legacy_weighted:>9.1f} {new_weighted:>9.1f}  {tags_str}")

print()
print("=" * 120)
print("差异详细分析:")
print()
for item in structured:
    title = item.get("title", "?")
    reqs = item.get("requirements", {})
    tags = list(reqs.get("tags", []) or [])
    cat = (reqs.get("category", "") or "").strip()
    all_tags = tags + ([cat] if cat and cat.lower() not in ("unknown", "学科竞赛", "其他") else [])

    li = legacy._score_interest(user, item)
    ni, _ = score_interest(user, item, new_agent.synonym_groups)
    ov, sigs = conceptual_overlap_detail(interest_tags, all_tags, new_agent.synonym_groups)

    # 新版分母
    denom = max(len(interest_tags), len(all_tags), 1)
    continuous_score = 100.0 * ov / denom

    print(f"  [{title}]")
    print(f"    tags: {all_tags}")
    print(f"    overlap: {ov}")
    print(f"    ---旧版离散分段---")
    if ov >= 2:
        print(f"      overlap>=2 → 100.0")
    elif ov == 1:
        print(f"      overlap==1 → 70.0")
    else:
        print(f"      overlap==0 → 10.0")
    print(f"    ---新版连续比率---")
    print(f"      100 * {ov} / max({len(interest_tags)}, {len(all_tags)}, 1)")
    print(f"      = {continuous_score:.1f}")
    print(f"    ---对比---")
    print(f"      旧版: {li:.1f}  新版: {ni:.1f}  差值: {ni - li:+.1f}")
    print()
