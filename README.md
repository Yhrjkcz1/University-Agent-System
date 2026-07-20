# 赛智通 Multi-Agent Demo

赛智通是面向大学生科研竞赛申请的轻量级多智能体辅助系统。

## 项目结构

```text
.
├── agents/            # 主 Agent 与各业务子 Agent
├── config/            # 可提交的非敏感配置
├── data/              # 项目数据目录（运行产物不提交）
├── docs/              # 项目说明文档
├── tests/             # 测试代码
├── app.py             # Gradio 网页应用
├── main.py            # 应用入口
└── requirements.txt   # Python 依赖
```

## 本地运行

```bash
pip install -r requirements.txt
python app.py
```

局域网访问：

```bash
python app.py --host 0.0.0.0 --port 7860
```

其他成员可访问 `http://你的电脑局域网IP:7860`。需要 Gradio 临时公网链接时可运行 `python app.py --share`。

## LLM 配置

请复制 `.env.example` 为 `.env`，然后在 `.env` 中填写 API Key：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat
```

`.env` 已被 Git 忽略，不会上传。未设置 API Key 时，`MainAgent` 会使用基于规则的后备规划逻辑。

## 当前状态

网页会调用 `agents/main_agent.py`。目前部分子 Agent 尚未实现，执行完整流程时相应状态可能显示为 `skipped`，这是当前阶段的预期行为。

后续可在对应文件中实现约定的 Agent 类及 `run(input_data: dict) -> dict` 方法，网页和 `MainAgent` 即可直接调用。

更多设计说明见 [`docs/PROJECT_SPEC_CN.md`](docs/PROJECT_SPEC_CN.md)。
