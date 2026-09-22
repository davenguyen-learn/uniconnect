import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('c:/Users/Admin/Code/uniconnect-v2/bao-cao/scratch/test_diagrams.py', encoding='utf-8') as f:
    text = f.read()

import re
d5 = re.search(r'diagram5 = r"""(.*?)"""', text, re.DOTALL).group(1)
lines = d5.splitlines()
for i, l in enumerate(lines, 1):
    if i in [36, 37, 38, 39]:
        print(f"{i}: {repr(l)}")
