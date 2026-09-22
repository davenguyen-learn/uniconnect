import os
import re
import glob

sections_dir = 'c:/Users/Admin/Code/uniconnect-v2/bao-cao/Sections'
tex_files = glob.glob(os.path.join(sections_dir, '*.tex'))
tex_files.append('c:/Users/Admin/Code/uniconnect-v2/bao-cao/main.tex')

print(f"Auditing {len(tex_files)} LaTeX files...")

banned_patterns = [
    (r'\bCLB\b', "CLB"),
    (r'câu lạc bộ', "câu lạc bộ"),
    (r'điểm rèn luyện', "điểm rèn luyện"),
    (r'Radar GPS 1-Chạm', "Radar GPS 1-Chạm"),
]

issues = []

for tf in tex_files:
    fname = os.path.basename(tf)
    with open(tf, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines, 1):
        # Ignore comments
        stripped = line.strip()
        if stripped.startswith('%'):
            continue
        
        for pat, desc in banned_patterns:
            if re.search(pat, line, re.IGNORECASE):
                issues.append(f"[{fname}:{i}] Found banned term '{desc}': {line.strip()[:80]}")

import sys
sys.stdout.reconfigure(encoding='utf-8')

print(f"Banned terms found: {len(issues)}")
for iss in issues:
    print("  ", iss)

# Check table and figure label matches
labels = set()
refs = []
for tf in tex_files:
    with open(tf, 'r', encoding='utf-8') as f:
        content = f.read()
        for m in re.finditer(r'\\label\{([^}]+)\}', content):
            labels.add(m.group(1))
        for m in re.finditer(r'\\ref\{([^}]+)\}', content):
            refs.append((os.path.basename(tf), m.group(1)))

missing_refs = [r for r in refs if r[1] not in labels and not r[1].startswith('sec:')]
print(f"Total labels: {len(labels)}, Total refs: {len(refs)}")
print(f"Missing ref targets: {len(missing_refs)}")
for mr in missing_refs:
    print(f"   Missing ref: {mr[1]} in {mr[0]}")
