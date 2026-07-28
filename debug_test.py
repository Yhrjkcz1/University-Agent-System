"""Quick debug test for MainAgent."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
from agents.main_agent import MainAgent

agent = MainAgent(config={})
result = agent.run({
    'task_id': 'test_001',
    'user_input': '我是计算机专业大二学生，推荐AI竞赛',
    'task_type': 'recommendation',
    'user_profile': {'major': '计算机科学与技术', 'grade': '大二'},
    'context': {},
    'input_data': {},
    'history': [],
    'required_output': 'markdown',
    'metadata': {'source': 'test'}
})

print('Status:', result.get('status'))
data = result.get('data', {})
print('Final Answer:', data.get('final_answer','')[:200])
agent_results = data.get('agent_results', [])
print(f'Number of agent results: {len(agent_results)}')
for r in agent_results:
    print(f'  Agent: {r.get("agent_name")}, Status: {r.get("status")}')
    rdata = r.get('data', {})
    recs = rdata.get('recommendations', [])
    print(f'  Recommendations count: {len(recs)}')
    if recs:
        print(f'  First rec title: {recs[0].get("title", "N/A")}')
