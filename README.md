# 赛智通（SaiZhiTong）

赛智通是面向大学生科研与竞赛场景的多智能体对话助手。系统通过连续对话了解用户的专业、年级、技能、兴趣和参赛目标，并协同完成竞赛信息采集、通知结构化抽取、个性化推荐、竞赛详情解释、收藏管理和 Word 报名材料生成。

> 当前版本适用于课程设计、竞赛展示、科研演示和内部试用。竞赛信息、推荐结果及生成材料仅供辅助决策；正式报名或提交前必须以赛事官网为准并人工复核。

## 项目状态

- 当前分支：`main`
- 生产架构：React + GitHub Pages、FastAPI + Render、Supabase、GitHub Actions
- 本地验收基线（2026-08-05）：前端生产构建通过；后端测试 158 项通过、9 项失败、3 项收集错误
- 当前结论：已具备内部预验收形态，完成数据库迁移、CORS 配置和回归修复后再进行正式验收

详细状态和整改项见：

- [项目评审报告](docs/PROJECT_REVIEW_2026-08-05.md)
- [验收与演示指南](docs/ACCEPTANCE_GUIDE_CN.md)
- [中文项目规范](docs/PROJECT_SPEC_CN.md)
- [English Project Specification](docs/PROJECT_SPEC.md)

## 核心能力

- **自然语言连续对话**：MainAgent 识别用户意图、维护状态并调度其他 Agent。
- **用户画像补全**：收集专业、年级、技能、方向、竞赛级别和时间偏好。
- **竞赛信息采集**：支持赛氪、52竞赛、天池、和鲸和 DataFountain 等来源。
- **通知结构化抽取**：提取名称、主办方、报名时间、比赛时间、类别、级别、官网及附件。
- **个性化推荐**：结合用户画像、硬性条件、兴趣与截止时间筛选并排序。
- **上下文追问**：支持“详细介绍第二个”“给刚才那个生成材料”等指代。
- **Word 材料生成**：生成可编辑的个人简历、报名表、项目材料和准备计划初稿。
- **账户与会话**：支持注册登录、JWT、会话历史、用户画像、收藏和管理员页面。
- **异步数据刷新**：网页或定时任务触发 GitHub Actions，不阻塞在线对话。
- **降级运行**：LLM 不可用时保留规则型基础流程并返回明确提示。

## 系统架构

```text
React / GitHub Pages
        │ HTTPS + JWT
        ▼
FastAPI / Render
        │
        ├── MainAgent：意图识别、上下文、任务调度、结果整合
        ├── InfoCollectAgent：公开竞赛数据与文件采集
        ├── InfoExtractAgent：通知字段结构化抽取
        ├── RecommendationAgent：候选筛选、排序与解释
        └── MaterialAgent：Word 材料生成
        │
        ├── Supabase：竞赛库、账户、会话、画像、收藏、刷新任务
        └── GitHub Actions：每日及手动竞赛库刷新
```

主要业务链路：

```text
竞赛推荐：补全画像 → 读取 Supabase 候选 → 筛选与排序 → 推荐解释
详情追问：读取本轮推荐上下文 → 定位竞赛 → 返回详情与待核实项
材料生成：确认目标竞赛 → 选择材料类型 → 生成 Word → 下载
数据刷新：采集各来源 → 比较内容哈希 → 抽取新增/变化记录 → 写入 Supabase
```

## 项目结构

```text
.
├── agents/                         # MainAgent 与四个业务 Agent
│   ├── info_collect/               # 数据源客户端、解析器与存储层
│   └── ReAgent_New/                # 推荐排序实现
├── auth/                           # JWT、账户与会话服务
├── config/                         # 非敏感配置和提示词模板
├── docs/                           # 规范、评审和验收材料
├── frontend/                       # React + TypeScript + Vite 前端
├── scripts/                        # 数据刷新及任务状态脚本
├── tests/                          # 自动化测试
├── api.py                          # FastAPI 生产入口
├── streamlit_app.py                # 本地兼容调试入口
├── app.py                          # Gradio 兼容调试入口
├── migration.sql                   # 竞赛和刷新相关数据库迁移
├── migration_auth.sql              # 账户、会话及补充迁移
├── render.yaml                     # Render 后端部署配置
└── requirements.txt                # Python 核心依赖
```

## 环境要求

- Python 3.11
- Node.js 20 与 npm
- Supabase 项目
- DeepSeek API Key（推荐；缺失时部分能力降级）
- GitHub Token（仅在网页触发 Actions 刷新时需要）

建议使用独立 Python 虚拟环境，避免与系统或 Anaconda 共享环境中的包冲突。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

前端依赖：

```powershell
Set-Location frontend
npm install
```

## 环境变量

复制示例文件：

```powershell
Copy-Item .env.example .env
```

主要变量：

| 变量 | 用途 | 部署位置 |
|---|---|---|
| `DEEPSEEK_API_KEY` | LLM 对话、抽取和材料生成 | Render、GitHub Actions、本地后端 |
| `SUPABASE_URL` | Supabase 项目地址 | Render、GitHub Actions、本地后端 |
| `SUPABASE_ANON_KEY` | 后端受限读取或兼容配置 | Render、GitHub Actions、本地后端 |
| `SUPABASE_SERVICE_ROLE_KEY` | 服务端写入和管理操作 | Render、GitHub Actions；禁止放入前端 |
| `SUPABASE_DB_PASSWORD` | 可选的 PostgreSQL 直连建表 | 本地或受保护服务端 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | Render、本地后端 |
| `ALLOWED_ORIGINS` | 允许访问 API 的前端 Origin | Render、本地后端 |
| `GITHUB_ACTIONS_TOKEN` | 从后端触发刷新工作流 | Render |
| `REFRESH_IP_HASH_SALT` | 刷新接口限流哈希盐 | Render |
| `ENABLE_LOCAL_EMBEDDING` | 是否启用本地 ONNX embedding | 默认 `false` |

不要提交真实 `.env`、API Key、数据库密码、JWT 密钥或 service-role key。

## 数据库初始化与升级

在 Supabase SQL Editor 依次执行：

1. `migration.sql`
2. `migration_auth.sql`

每次拉取包含数据库字段变更的版本后，都应重新执行幂等迁移。当前 API 会读取 `competitions.summary`；数据库未升级时，竞赛库接口会返回 503。

数据库主要包含：

- `competitions`：竞赛信息、摘要、日期、来源和抽取状态
- `crawl_logs`、`refresh_jobs`、`refresh_tokens`：采集与刷新任务
- `profiles`、`login_attempts`：账户和安全记录
- `conversations`、`user_portraits`：会话和用户画像
- `saved_competitions`：用户收藏

## 本地运行

启动后端：

```powershell
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

启动前端：

```powershell
Set-Location frontend
$env:VITE_API_BASE_URL="http://localhost:8000"
npm run dev
```

访问：

- 前端：`http://localhost:5173`
- 后端健康检查：`http://localhost:8000/`
- OpenAPI：`http://localhost:8000/docs`

兼容调试入口：

```powershell
streamlit run streamlit_app.py
python app.py
```

生产验收应以 React + FastAPI 链路为准，不以 Streamlit 或 Gradio 入口代替。

## 自动化检查

后端测试：

```powershell
python -m pytest tests -q -p no:cacheprovider
```

> 建议显式指定 `tests`。仓库根目录的 `test_crawler.py` 是手工诊断脚本，当前会被默认 pytest 规则误收集。

前端生产构建：

```powershell
Set-Location frontend
npm run build
```

推荐验收顺序：

1. 后端健康检查与 OpenAPI。
2. 竞赛库接口返回数据，而不是 503。
3. 注册、登录、刷新令牌和退出。
4. 用户画像补全与推荐。
5. 推荐详情追问和指代识别。
6. Word 材料生成与下载。
7. 收藏、会话恢复及管理员页面。
8. 手动刷新任务及状态查询。

## 部署

### 前端：GitHub Pages

`.github/workflows/deploy.yml` 在 `main` 更新后使用 Node.js 20 构建 `frontend/` 并部署到 GitHub Pages。生产 API 地址通过 `VITE_API_BASE_URL` 注入。

### 后端：Render

`render.yaml` 使用 Python 3.11 和以下启动命令：

```text
uvicorn api:app --host 0.0.0.0 --port $PORT
```

`ALLOWED_ORIGINS` 必须配置为真实 GitHub Pages Origin 或自定义域名，不能保留示例域名。

### 数据刷新：GitHub Actions

`refresh-competitions.yml` 支持：

- `workflow_dispatch` 手动触发；
- 每日 18:00 UTC，即次日北京时间 02:00 自动触发；
- 仅对新增或内容变化的记录重新抽取；
- 单一来源失败时保留其他来源结果并记录任务状态。

## 已知限制

- 公共网页结构变化、反爬策略和网络状态会影响采集结果。
- 竞赛日期和主办方必须以官方页面为最终依据。
- 当前部分 DataFountain 和 52竞赛日期解析测试未通过，正式验收前需要修复。
- 当前部分材料对话和异常提示测试未通过，存在流程回归风险。
- 免费 Render 实例可能休眠，首次访问会较慢。
- Render 512 MB 实例默认关闭本地 ONNX embedding，使用轻量排序方案。
- 前端构建主包较大，弱网首屏性能仍可优化。
- 未配置 Supabase 时，生产竞赛库、账户和会话能力不完整。
- 生成材料是可编辑初稿，不保证直接满足所有学校或赛事模板。

## 安全与隐私

- 不在公开环境输入身份证号、银行卡号、密码等敏感信息。
- service-role key、数据库密码和 JWT 密钥只能保存在受保护的服务端环境。
- 生成文件可能包含个人信息，下载后应及时检查并妥善保管。
- 正式报名和提交前必须人工核验全部内容。

## 许可与用途

本仓库当前主要用于教学、竞赛与研究演示。如需公开运营，应补充明确的软件许可证、隐私政策、数据来源合规说明、用户协议和生产级运维方案。
