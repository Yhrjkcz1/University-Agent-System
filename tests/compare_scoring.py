"""对比旧版(legacy)和新版(ReAgent_New)兴趣评分差异"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.recommendation_agent_legacy import RecommendationAgent as LegacyAgent
from agents.ReAgent_New import RecommendationAgent as NewAgent
from agents.ReAgent_New.utils import load_config
from agents.ReAgent_New.scoring import score_interest
from agents.ReAgent_New.synonyms import conceptual_overlap_detail

with open(ROOT / 'tests' / 'fixtures' / 'recommendation_input_sample.json', encoding='utf-8') as f:
    sample = json.load(f)

config = load_config()
legacy = LegacyAgent(config)
new_agent = NewAgent(config)

structured = sample['input_data']['structured_items']
user = sample['user_profile']
interest_tags = user.get('interests', [])
w = 0.30  # 兴趣权重

print("=" * 130)
print(f"用户兴趣: {interest_tags}")
print(f"竞赛总数: {len(structured)}")
print("=" * 130)
print(f"{'竞赛名称':<28} {'旧版兴趣分':>9} {'新版兴趣分':>9} {'旧版兴趣加权':>11} {'新版兴趣加权':>11}  overlap  tags")
print("-" * 130)

for item in structured:
    title = (item.get('title') or '?')[:26]
    reqs = item.get('requirements', {})
    tags = list(reqs.get('tags', []) or [])
    cat = (reqs.get('category', '') or '').strip()
    excluded = ('unknown', '学科竞赛', '其他')
    all_tags = tags + ([cat] if cat and cat.lower() not in excluded else [])

    li = legacy._score_interest(user, item)
    ni, _ = score_interest(user, item, new_agent.synonym_groups)
    ov, _ = conceptual_overlap_detail(interest_tags, all_tags, new_agent.synonym_groups)

    lw = li * w
    nw = ni * w

    tags_str = str(tags[:4])[:28]
    print(f"{title:<28} {li:>9.1f} {ni:>9.1f} {lw:>11.1f} {nw:>11.1f}  ov={ov}  {tags_str}")

print()
print("=" * 130)
print(">> 根本原因分析:")
print("   旧版兴趣分 = 离散阈值: overlap>=2 -> 100, overlap==1 -> 70, overlap==0 -> 10")
print("   新版兴趣分 = 连续比率: 100 * overlap / max(len(interests), len(tags), 1)")
print()

# 列出每个竞赛的详细差异
diff_items = []
for item in structured:
    reqs = item.get('requirements', {})
    tags = list(reqs.get('tags', []) or [])
    cat = (reqs.get('category', '') or '').strip()
    excluded = ('unknown', '学科竞赛', '其他')
    all_tags = tags + ([cat] if cat and cat.lower() not in excluded else [])
    li = legacy._score_interest(user, item)
    ni, _ = score_interest(user, item, new_agent.synonym_groups)
    ov, _ = conceptual_overlap_detail(interest_tags, all_tags, new_agent.synonym_groups)
    diff = ni - li
    denom = max(len(interest_tags), len(all_tags), 1)
    tag_s = str(all_tags)[:45]

    if diff < -30:
        sym = "*** 大幅偏低"
    elif diff < -10:
        sym = "** 偏低"
    elif diff != 0:
        sym = "* 有偏差"
    else:
        sym = "= 一致"

    diff_items.append((diff, item.get('title', '?'), li, ni, ov, denom, sym, tag_s))

diff_items.sort()
for diff, title, li, ni, ov, denom, sym, tag_s in diff_items:
    print(f"   {title[:24]:<24}: 旧={li:.0f} 新={ni:.0f} diff={diff:+.0f}  ov={ov} denom={denom}  {sym}")
    print(f"     tags={tag_s}")

print()
print("=" * 130)
print(">> 关键结论:")
print("   1. overlap匹配逻辑完全相同(同义词组/子串匹配)")
print("   2. 评分公式不同: 离散阈值(100/70/10) -> 连续比率(100*ov/denom)")
print("   3. 新版无匹配基线为0分,旧版基线10分")
print("   4. 连续比率导致所有兴趣分系统性降低(尤其overlap=1时)")
print("   5. 最终综合分差异可达10-30分,影响排序")
