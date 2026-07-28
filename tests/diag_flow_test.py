"""端到端数据流诊断：模拟前端 → API → MainAgent → 推荐引擎"""
import json
import httpx

def main():
    # 模拟前端发送"我是计算机专业大二学生，对 AI 感兴趣"
    payload = {
        "user_input": "我是计算机专业大二学生，对 AI 感兴趣",
        "task_type": "full_process",
        "user_profile": {
            "major": "计算机",
            "interests": ["AI"],
            "goal": "",
            "matched": True
        },
        "context": {},
        "input_data": {},
        "history": []
    }

    print("=" * 70)
    print("步骤 | 检查项")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 步骤 1: 前端 extractKeywords 提取结果（模拟）
    # ------------------------------------------------------------------
    print("""
[步骤1] 前端 extractKeywords.ts 提取结果
-----------------------------------------""")
    print(f"  user_input:        {repr(payload['user_input'])}")
    prof = payload["user_profile"]
    print(f"  major (专业):      {repr(prof['major'])}")
    print(f"  interests (兴趣):  {prof['interests']}")
    print(f"  AI 在 interests 中: {'是 [YES]' if 'AI' in prof['interests'] else '否 [NO]'}")
    print(f"  人工智能在 interests 中: {'是' if '人工智能' in prof['interests'] else '否（原文写的是 AI 不是"人工智能"）'}")

    # ------------------------------------------------------------------
    # 步骤 2: 前端 sendMessage 发送到 API 的 JSON 结构
    # ------------------------------------------------------------------
    print("""
[步骤2] 前端 -> API 发送的 JSON 结构
-----------------------------------------""")
    print(f"  字段名: user_input={repr(payload['user_input'][:30])}...")
    print(f"  字段名: user_profile.major={repr(prof['major'])}")
    print(f"  字段名: user_profile.interests={prof['interests']}")
    print(f"  字段名: user_profile.matched={prof['matched']}")
    print(f"  字段名: task_type={repr(payload['task_type'])}")
    print(f"  字段名: context={payload['context']}")
    print(f"  字段名: input_data={payload['input_data']}")

    # ------------------------------------------------------------------
    # 步骤 3: 调用 API 验证
    # ------------------------------------------------------------------
    print("""
[步骤3] API 接收验证（直接调用 /api/agent/run）
-----------------------------------------""")
    
    # 先测试端口 8000（可能已有服务）
    for port in [8000, 8001]:
        try:
            r = httpx.post(
                f"http://localhost:{port}/api/agent/run",
                json=payload,
                timeout=5
            )
            print(f"  端口 {port}: 连接成功 [OK]")
            if r.status_code == 200:
                result = r.json()
                print(f"  API 返回 success: {result.get('success')}")
                resp = result.get("response", {})
                text = resp.get("text", "") or ""
                print(f"  API 返回 type: {resp.get('type')}")
                print(f"  API 返回 text (前200字): {text[:200]}")
                recs = resp.get("recommendations", [])
                print(f"  推荐数量: {len(recs)}")
                if recs:
                    for rec in recs[:3]:
                        ms = rec.get("matched_signals", [])
                        ums = rec.get("unmatched_signals", [])
                        print(f"    竞赛: {rec.get('title','?')[:30]}")
                        print(f"      总分:    {rec.get('match_score', '?')}")
                        print(f"      匹配信号: {ms}")
                        print(f"      不匹配: {ums[:5]}")
                        detail = rec.get("detail", {})
                        interest_score = detail.get("interest_score", "?")
                        ability_score = detail.get("ability_score", "?")
                        print(f"      兴趣分:  {interest_score}")
                        print(f"      能力分:  {ability_score}")
                else:
                    print("  WARNING: 无推荐结果返回!")
                return
        except httpx.ConnectError:
            print(f"  端口 {port}: 连接失败")
        except Exception as e:
            print(f"  端口 {port}: 错误 {type(e).__name__}: {str(e)[:200]}")
    
    print("  无法连接任何后端服务。请先启动 uvicorn api:app")


if __name__ == "__main__":
    main()
