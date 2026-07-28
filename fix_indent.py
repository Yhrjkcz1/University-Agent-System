#!/usr/bin/env python3
"""修复 info_extract_agent.py 的缩进问题"""

import re

with open('agents/info_extract_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: 8-space indented '        def process' -> 4-space '    def process'
# The block starts with '        def process(self, input_data: dict) -> dict:'
# and ends at the '    def _apply_source_fallbacks' line

old_process_block_pattern = (
    r'        def process\(self, input_data: dict\) -> dict:\n'
    r'            """智能提取：已有结构化数据的数据项跳过 LLM，仅对脏数据做 LLM 提取。\n'
    r'\n'
    r'            流程：\n'
    r'            1\. 检查 API 是否可用，不可用则全部用缓存数据/回退（不调 LLM）\n'
    r'            2\. 遍历 raw_items，区分「已有结构化数据」与「需 LLM 提取」\n'
    r'               - 已有 title\+organizer 非空 → 直接 convert 为输出格式（跳过 LLM）\n'
    r'               - 其余项 → 加入待提取队列\n'
    r'            3\. API 可用时：待提取队列分片批量调用 LLM（每片 ≤ MAX_BATCH_SIZE 条）\n'
    r'            4\. 批量失败或 API 不可用 → 用缓存已有的字段做 fallback\n'
    r'            """\n'
)

match = re.search(old_process_block_pattern, content)
if match:
    print('Found process block at', match.start())
else:
    print('Could not find process block pattern, trying literal search')

# Simpler approach: find the exact lines and fix them
lines = content.split('\n')

# Find the problematic lines
fix_count = 0
i = 0
while i < len(lines):
    stripped = lines[i].lstrip()
    indent = len(lines[i]) - len(stripped)
    
    if indent == 8 and stripped.startswith('def process('):
        # Fix: change 8 spaces to 4
        lines[i] = '    ' + lines[i][8:]
        fix_count += 1
        print(f'Fixed process def at line {i+1}')
    elif indent == 8 and stripped.startswith('def _use_cache_fallback('):
        lines[i] = '    ' + lines[i][8:]
        fix_count += 1
        print(f'Fixed _use_cache_fallback def at line {i+1}')
    elif indent == 10 and stripped.startswith('def _should_use_mock('):
        # This is INSIDE _call_llm_extract (indent 10 = 8+2). Move to class level.
        lines[i] = '    ' + lines[i][10:]  # 10 spaces -> 4 spaces
        fix_count += 1
        print(f'Fixed _should_use_mock def at line {i+1}')
    
    # Fix all 8-space body content inside process/_use_cache_fallback (between MAX_BATCH_SIZE and _apply_source_fallbacks)
    # The body is indented at 12 spaces (4+8=12) for first level
    # Already inside the method bodies, we need to reduce extra 4 spaces
    
    i += 1

# Now fix the body indentation of process and _use_cache_fallback
# These methods are between MAX_BATCH_SIZE line and _apply_source_fallbacks
# The body has 12 spaces indent that should be 8 spaces (4 for class + 4 for method)

start_fix = False
for i, line in enumerate(lines):
    stripped = line.lstrip()
    
    if 'MAX_BATCH_SIZE = 20' in line:
        start_fix = True
        continue
    
    if stripped.startswith('def _apply_source_fallbacks('):
        start_fix = False
        continue
    
    if start_fix:
        indent = len(line) - len(stripped)
        # After MAX_BATCH_SIZE, we have the 8-space '        def process'
        # Its body is at 12 spaces. We need:
        # 12 -> 8 (method body), 16 -> 12 (if/for body), 20 -> 16, etc.
        # The extra indent is 4 spaces
        if indent >= 12 and stripped and not stripped.startswith('#'):
            lines[i] = ' ' * (indent - 4) + lines[i][indent:]

# Also fix the _should_use_mock body indent (was at 8 spaces indent before, now at 4)
# After '    def _should_use_mock' we need to fix its body
found_should = False
for i, line in enumerate(lines):
    stripped = line.lstrip()
    if stripped.startswith('def _should_use_mock('):
        found_should = True
        continue
    if found_should:
        indent = len(line) - len(stripped)
        if stripped.startswith('def _call_api('):
            found_should = False
            continue
        if stripped and not stripped.startswith('#'):
            # Body of _should_use_mock should be at 8 spaces (4 for class + 4 for method)
            if indent > 8:
                lines[i] = ' ' * (indent - 4) + lines[i][indent:]

content = '\n'.join(lines)
with open('agents/info_extract_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f'Done. Fixed {fix_count} def lines.')
print('Verify with: Select-String -Path agents/info_extract_agent.py -Pattern "^        def|^    def|^          def"')
