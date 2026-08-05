# 赛智通项目规范

版本：v2.0

更新日期：2026-08-05

适用范围：当前 `main` 分支的开发、测试、部署和验收

## 1. 产品定位

赛智通是面向大学生竞赛场景的多智能体对话系统。系统帮助用户发现竞赛、理解通知、获得个性化推荐并生成可编辑材料，但不代替赛事官网、学校审核或用户的最终判断。

## 2. 生产架构

| 层次 | 技术 | 职责 |
|---|---|---|
| Web 前端 | React、TypeScript、Vite、Ant Design | 对话、竞赛库、收藏、账户与管理页面 |
| API 后端 | FastAPI、Pydantic、Uvicorn | Agent 接口、鉴权、数据读取、文件下载、刷新调度 |
| 智能体 | MainAgent + 四个业务 Agent | 理解、采集、抽取、推荐和材料生成 |
| 数据层 | Supabase / PostgreSQL | 竞赛、账户、会话、画像、收藏和刷新任务 |
| 异步任务 | GitHub Actions | 定时及手动竞赛库刷新 |
| 部署 | GitHub Pages + Render | 静态前端和 Python API |

Streamlit 和 Gradio 仅作为本地兼容调试入口，不作为生产验收主入口。

## 3. Agent 职责

### 3.1 MainAgent

文件：`agents/main_agent.py`

职责：

- 识别推荐、详情、通知分析、材料生成和无关对话等意图；
- 维护画像、推荐结果、目标竞赛及材料类型等状态；
- 根据任务动态调用业务 Agent；
- 合并结果并生成用户可理解的回答；
- 在外部服务失败时返回安全、明确的降级提示。

### 3.2 InfoCollectAgent

文件：`agents/info_collect_agent.py`

职责：

- 从注册数据源或本地通知文件采集原始内容；
- 标准化 URL、来源、标题和正文；
- 通过内容哈希识别新增、变化和未变化记录；
- 记录单来源失败，不因单点失败丢弃其他来源数据。

### 3.3 InfoExtractAgent

文件：`agents/info_extract_agent.py`

职责：

- 将原始通知转换为统一结构；
- 提取标题、主办方、报名日期、比赛日期、类别、级别和附件；
- 保留原始来源和待核实字段；
- LLM 不可用时使用规则降级，禁止把模拟数据伪装成真实结果。

### 3.4 RecommendationAgent

文件：`agents/recommendation_agent.py`，核心实现位于 `agents/ReAgent_New/`。

职责：

- 根据画像和硬性条件筛选候选竞赛；
- 综合兴趣、技能、年级、级别、截止时间和多样性排序；
- 区分主推荐、备选项和不推荐原因；
- 返回具体理由、风险和下一步行动建议。

### 3.5 MaterialAgent

文件：`agents/material_agent.py`

职责：

- 确认目标竞赛和材料类型；
- 生成可编辑 `.docx` 初稿；
- 文件名包含竞赛和材料类型；
- 不泄露模型错误、API 错误或 traceback；
- 明确提示用户人工核验。

## 4. 核心业务流程

### 4.1 推荐

```text
用户描述需求
→ MainAgent 补全必要画像
→ 从 Supabase 读取候选竞赛
→ RecommendationAgent 筛选与排序
→ MainAgent 返回推荐、理由、风险与下一步
```

推荐请求不应在用户会话中同步触发网页爬虫。

### 4.2 详情追问

```text
用户引用“第二个/刚才那个”
→ 从状态快照定位推荐项
→ 返回结构化详情、官网和待核实事项
```

### 4.3 材料生成

```text
确认目标竞赛
→ 确认材料类型
→ 收集材料必需信息
→ MaterialAgent 生成 Word
→ 注册临时下载地址
```

### 4.4 数据刷新

```text
定时或网页触发
→ GitHub Actions
→ 逐来源采集
→ 新增/变化检测
→ InfoExtractAgent
→ Supabase
→ 更新 refresh_jobs
```

## 5. API 规范

生产入口：`api.py`

主要接口：

| 路径 | 方法 | 用途 |
|---|---|---|
| `/` | GET | 健康检查 |
| `/api/agent/run` | POST | 执行一轮对话 |
| `/api/competitions` | GET | 查询竞赛库 |
| `/api/competitions/refresh` | POST | 创建刷新任务 |
| `/api/competitions/refresh/status` | GET | 查询刷新状态 |
| `/api/auth/register` | POST | 注册 |
| `/api/auth/login` | POST | 登录 |
| `/api/auth/refresh` | POST | 刷新令牌 |
| `/api/auth/me` | GET/PATCH/DELETE | 当前用户资料 |
| `/api/conversations` | GET/POST | 会话列表与保存 |
| `/api/saved-competitions` | GET | 收藏列表 |
| `/api/admin/*` | 多种 | 管理员接口 |

`POST /api/agent/run` 请求示例：

```json
{
  "user_input": "我是计算机专业大三学生，想参加人工智能竞赛",
  "state_snapshot": {}
}
```

响应必须包含：

- `success`
- `response`
- `state_snapshot`
- `metadata`

## 6. 对话状态规范

状态快照至少应支持：

- 当前意图和对话阶段；
- 专业、年级、技能、兴趣和级别偏好；
- 最近推荐结果；
- 当前选中的竞赛；
- 材料类型和已收集材料信息；
- 需要继续追问的字段。

状态应为 JSON 可序列化对象，不保存 API 客户端、文件句柄或不可序列化类实例。

## 7. 数据规范

竞赛结构至少包含：

```json
{
  "title": "竞赛名称",
  "url": "https://official.example/competition",
  "source": "saikr",
  "description": "原始或清洗后的描述",
  "summary": "结构化摘要",
  "organizer": "主办方",
  "regist_start": "YYYY-MM-DD",
  "regist_end": "YYYY-MM-DD",
  "contest_start": "YYYY-MM-DD",
  "contest_end": "YYYY-MM-DD",
  "category": "人工智能",
  "level": "国家级"
}
```

规则：

- 缺失值使用空字符串、空数组或 `null`，不得编造；
- 日期优先采用 `YYYY-MM-DD`；
- 必须保留来源 URL；
- 时区转换必须明确业务口径，避免日期跨天后与官网展示不一致；
- 正式推荐必须排除明确过期或不满足硬性条件的项目。

## 8. 数据库规范

数据库迁移文件：

1. `migration.sql`
2. `migration_auth.sql`

迁移必须保持幂等。代码增加新字段时，必须同步更新迁移、README 和部署检查清单。API 当前依赖 `competitions.summary`，数据库未迁移时属于阻塞性部署错误。

service-role key 只能用于服务端和 GitHub Actions。前端不得直连需要 service-role 权限的表。

## 9. 安全规范

- 生产环境必须显式设置 `JWT_SECRET_KEY`；
- `ALLOWED_ORIGINS` 只允许真实前端域名；
- 密码必须使用安全哈希保存；
- Access Token 应短期有效，Refresh Token 应支持吊销；
- 管理接口必须同时验证登录和管理员角色；
- 用户可见错误不得包含密钥、SQL、内部路径或 traceback；
- 文件下载令牌应随机、不可预测并设置合理生命周期；
- 日志不得记录密码、完整 Token 或密钥。

## 10. 代码和目录规范

- 新测试放在 `tests/`，手工诊断脚本不要使用 `test_*.py` 名称；
- 临时数据放入 `data/temp/` 或明确忽略的临时目录；
- 生成材料放入 `data/output/`；
- 非敏感配置放入 `config/`；
- 不修改既有 Agent 文件名和公共响应结构，除非同步更新调用方及测试；
- 广泛捕获异常时必须记录上下文或转换为明确领域错误。

## 11. 测试与质量门槛

正式合并前：

```powershell
python -m pytest tests -q -p no:cacheprovider
Set-Location frontend
npm run build
```

正式验收最低门槛：

- `tests/` 自动化测试全部通过；
- 前端生产构建无错误；
- 健康检查和 OpenAPI 正常；
- 竞赛库真实接口返回 200；
- 注册登录、推荐、详情、材料、收藏和刷新至少完成一次端到端验证；
- Supabase 已执行最新迁移；
- CORS 与生产 API 地址匹配；
- 不使用真实用户隐私数据进行公开演示。

## 12. 当前已知问题

截至 2026-08-05：

- 全量测试为 158 通过、9 失败、3 收集错误；
- 当前连接的 Supabase 缺少 `competitions.summary`；
- 部分 52竞赛和 DataFountain 日期解析测试失败；
- 部分材料对话与异常提示存在回归；
- 刷新统计字段存在兼容性问题；
- `render.yaml` 中 CORS 示例域名需要替换为真实域名；
- 前端主包体积仍可优化。

详见 `docs/PROJECT_REVIEW_2026-08-05.md`。
