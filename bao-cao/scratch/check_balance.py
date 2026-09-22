import re

def check_latex_balance(text):
    stack = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        # strip comments
        line_no_comment = re.sub(r'(?<!\\)%.*$', '', line)
        for j, char in enumerate(line_no_comment):
            if char in '{[(':
                stack.append((char, i, j+1))
            elif char in '}])':
                if not stack:
                    return False, f"Extra closing '{char}' at line {i}:{j+1}"
                opening, oi, oj = stack.pop()
                expected = {'{':'}', '[':']', '(':')'}[opening]
                if char != expected:
                    return False, f"Mismatched pair: '{opening}' at line {oi}:{oj} closed by '{char}' at line {i}:{j+1}"
    if stack:
        opening, oi, oj = stack[-1]
        return False, f"Unclosed '{opening}' from line {oi}:{oj}"
    return True, "Balanced"

print("Syntax checker ready.")
