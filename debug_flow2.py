"""Debug: trace sub-agent results detail."""
import json, sys
sys.path.insert(0, '.')
from agents.main_agent import MainAgent

agent = MainAgent(config={})

demo = {
    'task_id': 'demo_task_001',
    'user_input': 'Please recommend suitable research competitions and generate an application checklist.',
    'task_type': 'full_process',
    'user_profile': {'major': 'computer science', 'grade': 'junior'},
    'context': {},
    'input_data': {},
    'history': [],
    'required_output': 'markdown',
    'metadata': {'source': 'test'},
}

result = agent.process(demo)
data = result.get('data', {})
agent_results = data.get('agent_results', [])

# Find recommendation agent result
for ar in agent_results:
    if 'recommend' in ar.get('agent_name', ''):
        print('=== RECOMMENDATION AGENT RESULT ===')
        print(json.dumps(ar, ensure_ascii=False, indent=2)[:2000])
        break

# Also check final_answer
fa = data.get('final_answer')
print()
print('=== FINAL ANSWER ===')
print(fa[:200])

# Check what _recommendations_from_agent_results returns
recs = MainAgent._recommendations_from_agent_results(agent_results)
print()
print(f'=== RECOMMENDATIONS FOUND: {len(recs)} ===')
if recs:
    print(json.dumps(recs[0], ensure_ascii=False, indent=2)[:500])
