import re

with open('Sections/5-Phan-tich-va-thiet-ke-he-thong.tex', 'r', encoding='utf-8') as f:
    lines = f.readlines()

with open('scratch/clb_matches.txt', 'w', encoding='utf-8') as out:
    for i, line in enumerate(lines, 1):
        if re.search(r'\b(CLB|câu lạc bộ|Câu lạc bộ)\b', line, re.IGNORECASE):
            out.write(f"{i}: {line.strip()}\n")

print("Done. Check scratch/clb_matches.txt")
