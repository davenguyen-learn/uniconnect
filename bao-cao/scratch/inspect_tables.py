import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
models_dir = 'c:/Users/Admin/Code/uniconnect-v2/server/app'
table_info = []

for root, dirs, files in os.walk(models_dir):
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            with open(filepath, encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
            matches = re.findall(r'__tablename__\s*=\s*[\'"]([^\'"]+)[\'"]', content)
            for m in matches:
                cls_match = re.search(r'class\s+(\w+)[^:]*?:\s*(?:[^\n]*?\n)*?\s*__tablename__\s*=\s*[\'"]' + re.escape(m) + r'[\'"]', content)
                cls_name = cls_match.group(1) if cls_match else 'Model'
                rel_path = os.path.relpath(filepath, 'c:/Users/Admin/Code/uniconnect-v2/server')
                table_info.append((m, cls_name, rel_path))

print(f"Total tables found in models: {len(table_info)}")
for t, c, p in sorted(table_info):
    print(f"- Table: {t:<28} Class: {c:<25} File: {p}")
