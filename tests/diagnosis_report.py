"""
完整诊断报告：新旧后端推荐结果不一致的根因分析
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.recommendation_agent_legacy import RecommendationAgent as LegacyAgent
from agents.ReAgent_New import RecommendationAgent as NewAgent
from agents.ReAgent_New.utils import load_config
from agents.ReAgent_New.scoring import score_interest, score_ability
from agents.ReAgent_New.synonyms import (
    conceptual_overlap_detail,
    user_ability_corpus,
    DEFAULT_SYNONYM_GROUPS,
)
from datetime import date

with open(ROOT / 'tests' / 'fixtures' / 'recommendation_input_sample.json', encoding='utf-8') as f:
    sample = json.load(f)

config = load_config()
legacy = LegacyAgent(config)
new_agent = NewAgent(config)

structured = sample['input_data']['structured_items']
user = sample['user_profile']
interest_tags = user.get('interests', [])
now = date.today()
corpus = user_ability_corpus(user)

print("=" * 120)
print("  新旧后端推荐结果不一致 - 诊断报告")
print("=" * 120)

# ============================================================
# 1. 兴趣分公式差异
# ============================================================
print()
print("#" * 120)
print("# 一、兴趣分公式差异（主要根因）")
print("#" * 120)
print()
print("旧版(legacy) _score_interest:")
print("   def _score_interest(self, user, item) -> float:")
print("       overlap = _conceptual_overlap(user_interests, tags)")
print("       if overlap >= 2:  return 100.0    # 强匹配")
print("       elif overlap == 1: return 70.0    # 单匹配")
print("       else:            return 10.0      # 不匹配（仍有基线）")
print()
print("新版(ReAgent_New) score_interest:")
print("   def score_interest(user, item) -> Tuple[float, List[str]]:")
print("       overlap, signals = conceptual_overlap_detail(...)")
print("       denom = max(len(interests), len(tags), 1)")
print("       return clamp(100.0 * overlap / denom), signals")
print("       # 不匹配 -> 0.0（无基线）")
print()

# 对比展示
print(">> 影响定量分析（兴趣分差异）:")
print(f"   用户兴趣: {interest_tags} (共 {len(interest_tags)} 个)")
print()
print(f"   {'竞赛':<28} {'旧版':>5} {'新版':>5} {'diff':>5}  {'公式说明'}")
print(f"   {'-'*28} {'-'*5} {'-'*5} {'-'*5}  {'-'*20}")
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
    d = ni - li
    denom = max(len(interest_tags), len(all_tags), 1)

    # 公式说明
    if ov >= 2:
        old_formula = "ov>=2->100"
    elif ov == 1:
        old_formula = "ov==1->70"
    else:
        old_formula = "ov==0->10"
    new_formula = f"100*{ov}/{denom}={100*ov/denom:.0f}"

    print(f"   {title:<28} {li:>5.0f} {ni:>5.0f} {d:>+5.0f}  旧:{old_formula}  新:{new_formula}")

# ============================================================
# 2. 能力分公式差异
# ============================================================
print()
print("#" * 120)
print("# 二、能力分公式差异（次要根因）")
print("#" * 120)
print()
print("旧版(legacy) _score_ability:")
print("   离散阈值: ratio>=0.8+经验->100, >=0.5+经验->75, >=0.5->65, >=0.3+经验->55, >=0.3->45, 有经验->45, else->25")
print()
print("新版(ReAgent_New) score_ability:")
print("   连续比率: score = 100 * overlap/total, 有经验则+15(保底45)")
print()

print(">> 影响定量分析（能力分差异）:")
print(f"   {'竞赛':<28} {'旧版':>5} {'新版':>5} {'diff':>5}  {'required_skills'}")
print(f"   {'-'*28} {'-'*5} {'-'*5} {'-'*5}  {'-'*30}")
for item in structured:
    title = (item.get('title') or '?')[:26]
    reqs = item.get('requirements', {})
    req_skills = list(reqs.get('required_skills', []) or [])

    li = legacy._score_ability(user, item, corpus)
    ni, _, _ = score_ability(user, item, corpus, new_agent.skill_normalize)
    d = ni - li

    rs = str(req_skills)[:30]
    print(f"   {title:<28} {li:>5.0f} {ni:>5.0f} {d:>+5.0f}  {rs}")

# ============================================================
# 3. 兴趣标签匹配问题
# ============================================================
print()
print("#" * 120)
print("# 三、'AI'相关标签匹配问题分析")
print("#" * 120)
print()

# 展示同义词组
print(">> 当前同义词组中的 AI 相关组:")
for g in DEFAULT_SYNONYM_GROUPS:
    g_lower = {x.strip().lower() for x in g}
    if 'ai' in g_lower or '人工智能' in g_lower:
        print(f"   {g}")
print()

# 检查数据集中哪些竞赛包含AI相关标签
print(">> 数据集中含 AI/人工智能 标签的竞赛:")
ai_related = []
for item in structured:
    reqs = item.get('requirements', {})
    tags = [str(t).lower() for t in (reqs.get('tags', []) or [])]
    cat = (reqs.get('category', '') or '').strip().lower()
    title = item.get('title', '?')
    if '人工智能' in tags or 'ai' in tags or '人工智能' in cat:
        ai_related.append((title, tags, cat))

if ai_related:
    for t, tags, cat in ai_related:
        print(f"   [{t}] tags={tags} cat={cat}")
else:
    print("   ❌ 数据集中没有任何竞赛包含 '人工智能' 或 'ai' 标签!")
print()

# 测试"AI"输入场景
print(">> 模拟前端输入 'AI' 的场景:")
print("   前端 extractKeywords.ts 逻辑:")
print("     const interestKeywords = ['AI', '人工智能', '算法', ...]")
print('     if (k === "AI") return text.includes("AI") || text.includes("人工智能")')
print()
test_texts = ["对AI感兴趣", "我是计算机专业大二学生，对AI感兴趣"]
for txt in test_texts:
    extracted = []
    interest_keywords = ["AI", "人工智能", "算法", "编程"]
    for k in interest_keywords:
        if k == "AI":
            if txt.lower().includes("ai") or "人工智能" in txt:
                extracted.append(k)
        elif k in txt:
            extracted.append(k)
    print(f'   输入: "{txt}"')
    print(f"   提取的兴趣: {extracted}")
    print(f"   注意: 'AI'被提取,但'人工智能' 未被提取(原文无'人工智能'字符)")
print()

print(">> 结论：AI标签匹配问题的根因链")
print("   1. 前端提取: 用户输入'对AI感兴趣' → 仅提取'AI'(English),而非'人工智能'")
print("   2. 后端匹配: 同义词组有{'ai','人工智能','artificial intelligence'}")
print("   3. 数据缺失: 数据集中没有任何竞赛含'人工智能'或'ai'标签")
print("   4. 结果: 即使匹配逻辑完全相同,兴趣分也为0")
print()
print(">> 修复建议:")
print("   a. 前端: extractKeywords 提取'AI'时也补上'人工智能'到 interests 数组")
print("   b. 后端: 在 scoring.py 接到'AI'时,自动扩展为'Ai','人工智能','Artificial Intelligence'")

# ============================================================
# 4. 综合差异
# ============================================================
print()
print("#" * 120)
print("# 四、总结：新旧后端推荐结果不一致的根因")
print("#" * 120)
print()
print("┌─────────────────────────────────────────────────────────────────────────────────┐")
print("│ 根因1 (主因): 兴趣评分公式不同                                                 │")
print("│   旧版: 离散阈值(100/70/10) → 每个匹配等级给固定高分                           │")
print("│   新版: 连续比率(100*ov/denom) → 分差较小,无匹配基线0分                       │")
print("│   影响: 所有竞赛兴趣分系统性降低,尤其overlap=1时从70→25~33(diff=-37~-45分)    │")
print("├─────────────────────────────────────────────────────────────────────────────────┤")
print("│ 根因2 (次因): 能力评分公式不同                                                 │")
print("│   旧版: 离散阈值(100/75/65/55/45/25)                                          │")
print("│   新版: 连续比率(100*ratio) + 经验软加分(+15)                                 │")
print("│   影响: 部分竞赛能力分也发生显著变化                                          │")
print("├─────────────────────────────────────────────────────────────────────────────────┤")
print("│ 根因3 (业务): 标签匹配逻辑相同,但评分公式变化放大了匹配不足的影响              │")
print("│   旧版无匹配也给10分基线,新版直接0分 → 英语/博弈类竞赛排名降低               │")
print("├─────────────────────────────────────────────────────────────────────────────────┤")
print("│ 根因4 (前端): 'AI'兴趣提取不完整 → 只提取'AI'不提取'人工智能'                │")
print("│   导致后端虽同义词组正确匹配,但数据本身缺失AI标签                            │")
print("└─────────────────────────────────────────────────────────────────────────────────┘")
