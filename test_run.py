"""Quick end-to-end test of MainAgent."""
from agents.main_agent import MainAgent

agent = MainAgent(config={})
result = agent.run({
    "task_id": "test_001",
    "user_input": "我是计算机专业大二学生，想找竞赛",
    "task_type": "recommendation",
    "user_profile": {},
    "context": {},
    "input_data": {},
    "history": [],
    "required_output": "markdown",
    "metadata": {"source": "test"},
})
print(f"Status: {result.get('status')}")
print(f"Message: {str(result.get('message'))[:100]}")
data = result.get("data", {})
answer = data.get("final_answer", "") or ""
if answer:
    print(f"Final answer: {answer[:200]}")
else:
    print("No final_answer")
print("Agent run completed successfully!")
