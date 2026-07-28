"""Find and fix inconsistent indentation in string continuations."""
import re

with open('agents/main_agent.py', encoding='utf-8-sig') as f:
    content = f.read()
    lines = content.split('\n')

# Find all string continuation issues (lines where a string follows another string
# inside parentheses with different indentation)
issues = []
for i in range(1, len(lines)):
    curr = lines[i].rstrip()
    prev = lines[i-1].rstrip()
    if not curr or not prev:
        continue
    
    ci = len(curr) - len(curr.lstrip())
    pi = len(prev) - len(prev.lstrip())
    
    curr_stripped = curr.lstrip()
    prev_stripped = prev.lstrip()
    
    # Check if both are string continuation lines (start/end with quote)
    curr_is_str = curr_stripped.startswith('"') and curr_stripped.endswith('"')
    prev_is_str = prev_stripped.startswith('"') and prev_stripped.endswith('"')
    
    if curr_is_str and prev_is_str and ci != pi:
        issues.append((i+1, pi, ci, prev[:80], curr[:80]))

print(f'Found {len(issues)} indentation issues:')
for line_num, pi, ci, prev, curr in issues:
    print(f'Line {line_num}: should be {pi} spaces, has {ci} spaces')
    print(f'  Prev: {prev}')
    print(f'  Curr: {curr}')
    print()
