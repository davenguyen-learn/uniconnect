import sys
sys.stdout.reconfigure(encoding='utf-8')
from test_diagrams import diagram3, check_latex_balance
import re

lines = diagram3.splitlines()
for i, l in enumerate(lines, 1):
    print(f"{i}: {l}")
