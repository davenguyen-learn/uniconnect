import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

routers_dir = 'c:/Users/Admin/Code/uniconnect-v2/server/app/modules'
endpoints = []

for root, dirs, files in os.walk(routers_dir):
    for f in files:
        if f.endswith('.py') and ('router' in f or 'api' in f or 'endpoints' in f):
            filepath = os.path.join(root, f)
            module_name = os.path.basename(os.path.dirname(filepath))
            with open(filepath, encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
            # find @router.get, post, put, delete, patch
            matches = re.findall(r'@(?:router|api_router)\.(get|post|put|delete|patch)\([\'"]([^\'"]+)[\'"]', content)
            for method, path in matches:
                endpoints.append((module_name, method.upper(), path))

print(f"Total API endpoints found: {len(endpoints)}")
for m, meth, p in sorted(endpoints):
    print(f"- [{m:<15}] {meth:<6} {p}")
