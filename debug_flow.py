"""Debug: trace sub-agent results."""
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
print(f'Status: {result.get("status")}')
print(f'Num agent_results: {len(agent_results)}')
for ar in agent_results:
    an = ar.get('agent_name', 'unknown')
    st = ar.get('status', 'unknown')
    msg = str(ar.get('message', ''))[:120]
    d = ar.get('data', {})
    has_recs = bool(d.get('recommendations'))
    has_raw = bool(d.get('raw_items'))
    has_ex = bool(d.get('extracted_items') or d.get('structured_items'))
    print(f'  [{an}] status={st} msg={msg!r}')
    print(f'         has_recs={has_recs} has_raw={has_raw} has_extracted={has_ex}')
    if has_recs:
        recs = d.get('recommendations', [])
        print(f'         recs_count={len(recs)}')
