"""测试聊天 API"""
import urllib.request, json

data = json.dumps({
    'user_input': '我是计算机专业大二的，对AI和编程感兴趣，有什么竞赛推荐？',
    'task_type': 'full_process',
    'user_profile': {},
    'context': {},
    'input_data': {},
    'history': []
}).encode()

req = urllib.request.Request(
    'http://localhost:8000/api/agent/run',
    data=data,
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    resp = urllib.request.urlopen(req, timeout=120)
    result = json.loads(resp.read())
    text = result.get('response', {}).get('text', '')
    print('=== 回复文本 ===')
    print(text[:1500])
    print('... (截断)')
    recs = result.get('response', {}).get('recommendations', [])
    print(f'\n=== 推荐数量: {len(recs)} ===')
    for i, r in enumerate(recs[:3]):
        title = r.get('title', '?')[:50]
        score = r.get('match_score', '?')
        signals = r.get('matched_signals', [])
        print(f'  {i+1}. {title}')
        print(f'     评分: {score} | 匹配信号: {signals}')
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
