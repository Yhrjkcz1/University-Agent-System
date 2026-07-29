"""API 服务层：为前端 third-web 提供 RESTful API 接口。

用法
----
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
import logging
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.main_agent import MainAgent

# ---------------------------------------------------------------------------
# 临时诊断日志
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="[DIAG] %(asctime)s %(message)s")
logger = logging.getLogger("api_diagnosis")

# ---------------------------------------------------------------------------
# 项目路径与配置加载
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def load_config() -> dict:
    """加载 YAML 配置，失败时返回空 dict。"""
    if not CONFIG_PATH.exists():
        return {}
    try:
        import yaml
    except ImportError:
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    return data if isinstance(data, dict) else {}


# ---------------------------------------------------------------------------
# 请求 / 响应数据模型
# ---------------------------------------------------------------------------


class AgentRunRequest(BaseModel):
    """前端 POST /api/agent/run 请求体。"""
    user_input: str = ""
    task_type: str = "full_process"
    user_profile: dict[str, Any] = {}
    context: dict[str, Any] = {}
    input_data: dict[str, Any] = {}
    history: list[dict[str, str]] = []


class AgentRunResponse(BaseModel):
    """返回给前端的统一响应结构。"""
    success: bool
    response: dict[str, Any]


# ---------------------------------------------------------------------------
# 构建 MainAgent.run() 标准输入
# ---------------------------------------------------------------------------


def build_minimal_input(
    user_input: str,
    task_type: str,
    user_profile: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    input_data: dict[str, Any] | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """构建标准输入，兼容 MainAgent.run() 的所有必填字段。

    优先使用前端传递的已有状态，保持对话连续。
    """
    return {
        "task_id": f"api_task_{uuid.uuid4().hex[:8]}",
        "user_input": (user_input or "").strip(),
        "task_type": (task_type or "full_process").strip(),
        "user_profile": user_profile or {},
        "context": context or {},
        "input_data": input_data or {},
        "history": history or [],
        "required_output": "markdown",
        "metadata": {"source": "api", "ui_version": "2.0"},
    }


# ---------------------------------------------------------------------------
# FastAPI 应用实例
# ---------------------------------------------------------------------------

app = FastAPI(
    title="赛智通 Agent API",
    description="为前端 third-web 提供 Agent 调度 RESTful 接口",
    version="1.0.0",
)

# 允许前端跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# 会话管理（内存级，按首次会话指纹索引）
# ---------------------------------------------------------------------------


class SessionStore:
    """内存会话存储：用首次用户消息 + major 做稳定指纹。"""

    def __init__(self):
        self._sessions: dict[str, dict[str, Any]] = {}

    def _fingerprint(self, req: AgentRunRequest) -> str:
        """从请求中生成稳定的会话指纹（跨后续请求不变）。"""
        history = req.history or []
        first_user_msg = ""
        for m in history:
            if m.get("role") == "user":
                first_user_msg = m.get("content", "")
                break
        if not first_user_msg:
            first_user_msg = req.user_input or ""
        profile = req.user_profile or {}
        major = profile.get("major", "")
        raw = f"{major}|{first_user_msg[:100]}"
        return hashlib.md5(raw.encode()).hexdigest()

    def get_or_create(self, req: AgentRunRequest) -> dict[str, Any]:
        """获取或创建会话上下文。"""
        key = self._fingerprint(req)
        if key not in self._sessions:
            self._sessions[key] = {
                "recommendation_pool": [],
                "previous_result_data": None,
                "conversation_state": {},
            }
        return self._sessions[key]

    def store_result(self, req: AgentRunRequest, result_data: dict[str, Any], pool: list):
        """保存推荐结果到会话。"""
        key = self._fingerprint(req)
        if key in self._sessions:
            self._sessions[key]["recommendation_pool"] = pool
            self._sessions[key]["previous_result_data"] = result_data


session_store = SessionStore()


# ---------------------------------------------------------------------------
# 对话路由工具函数
# ---------------------------------------------------------------------------


def _is_more_recommendations_request(user_input: str) -> bool:
    """判断用户是否在请求「更多推荐」。"""
    if not user_input:
        return False
    text = user_input.strip()
    # 匹配「还有其他推荐吗」「更多推荐」「换一批」「别的推荐」「再推荐一些」等常见表达
    more_keywords = [
        "其他", "更多", "换一批", "别的", "另外的", "再看看",
        "还有", "再推荐", "其他推荐", "更多推荐", "其他项目",
        "别的推荐", "其他比赛", "更多选项", "更多选择",
    ]
    return any(kw in text for kw in more_keywords)


def _build_more_recommendations_response(
    pool: list[dict[str, Any]],
    already_shown: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """从候选池中取出未展示过的推荐，构造扩容回复。"""
    if not pool:
        return None
    shown_titles = {
        r.get("title", "") for r in already_shown if isinstance(r, dict)
    }
    # 从池中取未展示过的（跳过已展示的标题）
    fresh: list[dict[str, Any]] = []
    for item in pool:
        if len(fresh) >= 3:
            break
        title = item.get("title", "")
        if title and title not in shown_titles:
            fresh.append(item)
            shown_titles.add(title)
    if not fresh:
        # 没有新项目可推荐
        return {
            "text": "目前符合条件的竞赛候选都已经展示过了。你可以换个专业方向或调整筛选条件，我再帮你重新查找。",
            "type": "agent",
            "files": [],
            "recommendations": [],
        }
    names = "、".join(r.get("title", "") for r in fresh)
    text = f"除了前面推荐的，以下项目也值得关注：{names}。你可以继续问我其中某个竞赛的详情。"
    return {
        "text": text,
        "type": "result",
        "files": [],
        "recommendations": fresh,
    }


# ---------------------------------------------------------------------------
# 路由
# ---------------------------------------------------------------------------


@app.get("/")
def health_check() -> dict[str, str]:
    """健康检查端点，供 Render 等平台探测。"""
    return {"status": "ok", "service": "saizhitong-agent-api"}


@app.post("/api/agent/run", response_model=AgentRunResponse)
def run_agent(req: AgentRunRequest) -> AgentRunResponse:
    """【核心接口】接收前端请求 → 对话路由 → 调度 MainAgent → 返回结果。"""
    try:
        # ---------------------------------------------------------------
        # [DIAG] 打印前端传来的完整请求
        # ---------------------------------------------------------------
        logger.info("=" * 80)
        logger.info("[STEP 1] 收到前端请求")
        logger.info(f"  user_input: {repr(req.user_input)}")
        logger.info(f"  task_type:  {repr(req.task_type)}")
        logger.info(f"  user_profile (原始): {json.dumps(req.user_profile, ensure_ascii=False)}")
        logger.info(f"  context keys: {list(req.context.keys()) if req.context else 'empty'}")
        logger.info(f"  history turns: {len(req.history)}")

        config = load_config()
        agent = MainAgent(config=config)

        # ---------------------------------------------------------------
        # 用户输入预处理：获取稳定会话
        # ---------------------------------------------------------------
        session = session_store.get_or_create(req)
        user_text = str(req.user_input or "").strip()

        # ---------------------------------------------------------------
        # Step A: 问候 / 致谢 / 越界 → handle_conversation_control()
        # ---------------------------------------------------------------
        cc_result = agent.handle_conversation_control(
            user_text,
            conversation_state=session.get("conversation_state"),
        )
        if cc_result is not None:
            final_answer = (
                cc_result.get("data", {}).get("final_answer")
                or "你好，有什么可以帮你的？"
            )
            logger.info(f"  [路由] 对话控制处理 → {cc_result.get('metadata', {}).get('followup_type', 'unknown')}")
            return AgentRunResponse(
                success=True,
                response={
                    "text": final_answer,
                    "type": "agent",
                    "files": [],
                    "recommendations": [],
                },
            )

        # ---------------------------------------------------------------
        # Step B: 用户画像校验 + 提取
        # ---------------------------------------------------------------
        profile = req.user_profile or {}
        major = str(profile.get("major") or "").strip()

        task_type = (req.task_type or "full_process").strip().lower()
        needs_profile = task_type in {"full_process", "recommend", "recommendation"}

        if needs_profile and not major:
            # 从前端传来的 user_input 中提取专业、兴趣、目标
            major_hint = _detect_major_in_text(user_text)
            if major_hint:
                req.user_profile["major"] = major_hint
                req.user_profile["grade"] = _detect_grade_in_text(user_text)
                # 重新获取 session（major 变了，指纹会重新生成）
                session = session_store.get_or_create(req)
            else:
                return AgentRunResponse(
                    success=False,
                    response={
                        "text": (
                            "我还不清楚你的专业和当前年级。\n\n"
                            "你可以这样告诉我：\n"
                            "• 「我是计算机科学与技术专业大二的学生」\n"
                            "• 「软件工程大三，想参加算法竞赛」\n"
                            "• 「电子信息工程大一，有推荐的比赛吗」\n\n"
                            "有了这些信息我才能帮你筛选真正适合的竞赛。"
                        ),
                        "type": "need_input",
                        "files": [],
                        "recommendations": [],
                    },
                )

        # 补充 interests 和 goal
        existing_interests = req.user_profile.get("interests", [])
        existing_goal = req.user_profile.get("goal", "")
        if not existing_interests:
            extracted_interests = _detect_interests_in_text(user_text)
            if extracted_interests:
                req.user_profile["interests"] = extracted_interests
                logger.info(f"  [画像增强] 从 user_input 提取 interests: {extracted_interests}")
        if not existing_goal:
            extracted_goal = _detect_goal_in_text(user_text)
            if extracted_goal:
                req.user_profile["goal"] = extracted_goal
                logger.info(f"  [画像增强] 从 user_input 提取 goal: {extracted_goal}")

        # ---------------------------------------------------------------
        # Step C: 多轮对话路由 —— 检查是否是对上一轮结果的追问
        # ---------------------------------------------------------------
        previous_result_data = session.get("previous_result_data")
        conversation_state = session.get("conversation_state", {})

        # C1: 用户请求「更多推荐」
        if _is_more_recommendations_request(user_text):
            pool = session.get("recommendation_pool", [])
            # 从 historical 中获取上一轮已展示的推荐
            already_shown: list[dict[str, Any]] = []
            if previous_result_data:
                already_shown = previous_result_data.get("recommendations", [])
            more_resp = _build_more_recommendations_response(pool, already_shown)
            if more_resp is not None:
                logger.info(f"  [路由] 扩容推荐响应 → 池大小: {len(pool)}, 已有: {len(already_shown)}")
                return AgentRunResponse(
                    success=True,
                    response=more_resp,
                )
            # 没有池或扩容失败，走 normal pipeline
            logger.info("  [路由] 请求更多推荐但候选池为空，回退到 normal pipeline")

        # C2: 追问详情/对比 → handle_followup()
        if previous_result_data is not None:
            followup_result = agent.handle_followup(
                user_text,
                previous_result_data.get("_raw_agent_output", {})
                if isinstance(previous_result_data, dict)
                else {},
                conversation_state=conversation_state,
            )
            if followup_result is not None:
                final_answer = (
                    followup_result.get("data", {}).get("final_answer")
                    or followup_result.get("message", "")
                )
                followup_type = followup_result.get("metadata", {}).get("followup_type", "unknown")
                logger.info(f"  [路由] 追问处理 → {followup_type}")
                # 如果是详情请求，附带对应的推荐对象
                detail_recs = []
                if followup_type == "competition_detail":
                    selected = followup_result.get("data", {}).get("selected_competition")
                    if selected:
                        detail_recs = [selected]
                return AgentRunResponse(
                    success=followup_result.get("status") in {"success", "partial"},
                    response={
                        "text": final_answer,
                        "type": "agent",
                        "files": [],
                        "recommendations": detail_recs,
                    },
                )

        # ---------------------------------------------------------------
        # Step D: 运行正常推荐管线
        # ---------------------------------------------------------------
        standard_input = build_minimal_input(
            user_input=req.user_input,
            task_type=req.task_type,
            user_profile=req.user_profile,
            context=req.context,
            input_data=req.input_data,
            history=req.history,
        )

        # 将历史对话注入 input_data，让 _build_final_answer 感知上下文
        standard_input["history"] = req.history or []
        standard_input["user_input"] = req.user_input or ""

        logger.info("[STEP 2] 构造的 standard_input 传给 MainAgent")
        logger.info(f"  user_input:     {repr(standard_input.get('user_input'))}")
        logger.info(f"  task_type:      {repr(standard_input.get('task_type'))}")
        logger.info(f"  user_profile:   {json.dumps(standard_input.get('user_profile'), ensure_ascii=False)}")
        logger.info(f"  history turns:  {len(standard_input.get('history', []))}")

        up = standard_input.get("user_profile", {})
        interests = up.get("interests", [])
        major_found = up.get("major", "")
        goal = up.get("goal", "")
        logger.info(f"  >>> 提取的画像: major={repr(major_found)}, interests={interests}, goal={repr(goal)}")
        if not interests:
            logger.warning("  *** WARNING: interests 仍为空! 兴趣分将全部为 0")

        result = agent.run(standard_input)

        # ---------------------------------------------------------------
        # Step E: 提取结果并保存会话
        # ---------------------------------------------------------------
        data = result.get("data", {})
        final_answer = (
            data.get("final_answer")
            or result.get("message", "")
        )
        if not final_answer:
            final_answer = "智能体执行完毕，但没有生成可展示的结果。"

        # 提取推荐列表和推荐池（从子 agent 结果中获取）
        recommendations_list: list[dict[str, Any]] = []
        recommendation_pool: list[dict[str, Any]] = []
        agent_results = data.get("agent_results", [])
        if isinstance(agent_results, list):
            for ar in agent_results:
                ar_data = ar.get("data", {}) if isinstance(ar, dict) else {}
                recs = ar_data.get("recommendations", [])
                if isinstance(recs, list) and recs:
                    recommendations_list = recs
                pool = ar_data.get("recommendation_pool", [])
                if isinstance(pool, list) and pool:
                    recommendation_pool = pool
                if recommendations_list and recommendation_pool:
                    break
        if not recommendations_list:
            recs = data.get("recommendations", [])
            if isinstance(recs, list) and recs:
                recommendations_list = recs
        if not recommendation_pool and recommendations_list:
            recommendation_pool = recommendations_list[:]

        # 保存到会话（供后续「更多推荐」/「详情」等追问复用）
        previous_result_data_saved = {
            "recommendations": recommendations_list,
            "recommendation_pool": recommendation_pool,
            "_raw_agent_output": result,
        }
        session_store.store_result(req, previous_result_data_saved, recommendation_pool)

        # 更新会话中的 conversation_state（从 understand_conversation_turn 获取）
        llm_state = agent.understand_conversation_turn(
            req.user_input or "",
            conversation_state=session.get("conversation_state", {}),
        )
        if llm_state and isinstance(llm_state, dict):
            logger.info(f"  [LLM 理解] dialogue_action={llm_state.get('dialogue_action', 'unknown')}")
            session["conversation_state"].update(llm_state)

        # 确定 response type
        status = result.get("status", "failed")
        has_recs = bool(recommendations_list)
        if status == "partial":
            response_type = "result" if has_recs else "agent"
        elif status == "need_input":
            response_type = "need_input"
        elif status == "failed":
            response_type = "error"
        else:
            response_type = "agent"

        return AgentRunResponse(
            success=status in {"success", "partial"},
            response={
                "text": final_answer,
                "type": response_type,
                "files": [],
                "recommendations": recommendations_list,
            },
        )

    except Exception as exc:
        logger.error(f"[错误] {exc}")
        return AgentRunResponse(
            success=False,
            response={
                "text": f"服务器内部错误：{exc}",
                "type": "error",
                "files": [],
                "recommendations": [],
            },
        )


def _detect_major_in_text(text: str) -> str:
    """从用户输入中简单检测专业名称。"""
    known_majors = [
        "计算机科学与技术", "软件工程", "网络工程", "信息安全", "数据科学",
        "人工智能", "电子信息工程", "通信工程", "自动化", "电气工程",
        "机械工程", "土木工程", "建筑学", "数学", "应用数学", "统计学",
        "物理", "化学", "生物", "材料科学", "工商管理", "会计", "金融",
        "法学", "新闻传播", "汉语言文学", "英语", "医学", "药学",
    ]
    for major in known_majors:
        if major in text:
            return major
    # 尝试匹配 "XX专业" 模式
    match = re.search(r"([\u4e00-\u9fff]{2,8})专业", text)
    if match:
        return match.group(1)
    return ""


def _detect_grade_in_text(text: str) -> str:
    """从用户输入中检测年级。"""
    grade_map = {
        "大一": "大一", "大二": "大二", "大三": "大三", "大四": "大四",
        "研一": "研究生", "研二": "研究生", "研三": "研究生",
        "研究生": "研究生", "硕士": "研究生", "博士": "研究生",
    }
    for keyword, grade in grade_map.items():
        if keyword in text:
            return grade
    return ""


def _detect_interests_in_text(text: str) -> list[str]:
    """从用户输入中提取兴趣关键词（与前端 extractKeywords.ts 保持一致的兴趣集）。

    支持中英文混合表达，如 '对AI和编程感兴趣' → ['AI', '编程']。
    """
    interest_keywords = [
        "AI", "人工智能", "算法", "编程", "开发", "创新", "创业", "建模",
        "数学建模", "大数据", "数据", "数据分析", "数据挖掘", "数据科学",
        "安全", "网络安全", "游戏", "前端", "后端", "全栈", "产品",
        "设计", "UI", "UX", "机器学习", "深度学习", "视觉", "计算机视觉",
        "自然语言", "自然语言处理", "NLP", "物联网", "IoT",
        "区块链", "云计算", "嵌入式", "机器人", "图像", "图像处理",
        "音频", "视频", "多媒体", "硬件", "电路", "芯片", "半导体",
        "生物", "生物信息", "化学", "材料", "物理", "天文",
        "金融", "金融科技", "经济", "商业", "营销", "市场",
        "法律", "法学", "教育", "心理", "心理学", "社会", "社会学",
        "文学", "写作", "翻译", "外语", "英语",
        "医疗", "医学", "药学", "制药", "环境", "环保", "能源",
        "交通", "物流", "供应链", "农业", "食品",
    ]
    detected: list[str] = []
    normalized = text.lower()
    for keyword in interest_keywords:
        if keyword == "AI":
            if "ai" in normalized or "人工智能" in text:
                detected.append("AI")
        elif keyword == "数学建模":
            if "数学建模" in text or "建模" in text:
                detected.append("数学建模")
        elif keyword == "自然语言处理" or keyword == "NLP":
            if "自然语言" in text or "nlp" in normalized:
                detected.append("自然语言处理")
        elif keyword == "大数据":
            if "大数据" in text:
                detected.append("大数据")
        elif keyword in text and keyword not in detected:
            # 避免短词误匹配：长度 <=2 的词需要独立单词边界
            if len(keyword) <= 2:
                if re.search(rf"{re.escape(keyword)}", text):
                    detected.append(keyword)
            else:
                detected.append(keyword)
    # 去重并保持顺序
    seen = set()
    result: list[str] = []
    for item in detected:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _detect_goal_in_text(text: str) -> str:
    """从用户输入中提取目标/动机（与前端 extractKeywords.ts 一致的分类）。

    按优先级返回最先匹配到的目标类别：
    国奖类 > 省奖类 > 名次类 > 升学就业 > 能力提升 > 奖金奖励 > 入门尝试 > 进阶挑战
    """
    goal_rules: list[tuple[list[str], str]] = [
        (["国奖", "国家级", "国家一等奖", "国家二等奖", "国家三等奖",
          "全国一等奖", "全国二等奖", "全国三等奖"], "国家级奖项"),
        (["省奖", "省级", "省一", "省二", "省三",
          "省级一等奖", "省级二等奖", "省级三等奖"], "省级奖项"),
        (["一等奖", "二等奖", "三等奖", "金奖", "银奖", "铜奖",
          "最高奖", "特等奖"], "高名次奖项"),
        (["保研", "综测", "加分", "奖学金", "简历", "留学",
          "考研", "就业", "找工作"], "升学就业"),
        (["提升经验", "参与", "体验", "锻炼", "能力", "技能",
          "实践机会", "增长见识", "涨经验"], "能力提升"),
        (["奖金", "奖励", "奖品", "现金"], "奖金奖励"),
        (["入门", "新手", "小白", "零基础", "初级", "基础", "尝试"], "入门尝试"),
        (["进阶", "挑战", "突破", "提升", "拔高", "高难度"], "进阶挑战"),
    ]
    for keywords, label in goal_rules:
        if any(kw in text for kw in keywords):
            return label
    return ""


# ---------------------------------------------------------------------------
# 直接运行时启动开发服务器
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
