"""Test the full conversation flow through app.py."""
from app import new_chat_state, _update_chat_state, _next_chat_question

# Start a new conversation
state = new_chat_state()
print(f"Initial state: intent={state.get('intent')}, major={state.get('major')}")

# Turn 1: User says hello
state = _update_chat_state(state, "你好")
print(f"After '你好': intent={state.get('intent')}")
question = _next_chat_question(state)
if question:
    print(f"  Question: {question[:80]}...")

# Turn 2: User introduces themselves
state = _update_chat_state(state, "我是计算机科学专业大三学生")
print(f"\nAfter intro: intent={state.get('intent')}, major={state.get('major')}, grade={state.get('grade')}")
question = _next_chat_question(state)
if question:
    print(f"  Question: {question[:80]}...")

# Turn 3: User wants competitions
state = _update_chat_state(state, "我想参加国家级人工智能竞赛")
print(f"\nAfter request: intent={state.get('intent')}, competition_type={state.get('competition_type')}, level={state.get('competition_level')}")
question = _next_chat_question(state)
if question:
    print(f"  Question: {question[:80]}...")

# Turn 4: User provides skills
state = _update_chat_state(state, "我会Python和Java，每周大概10小时")
print(f"\nAfter skills: skills={state.get('skills')}, available_time={state.get('available_time_per_week')}")
question = _next_chat_question(state)
if question:
    print(f"  Question: {question[:80]}...")
else:
    print("  No more questions (ready to dispatch)")


print("\n=== Conversation flow test completed! ===")
