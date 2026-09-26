import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

with open('bao-cao/scratch/benchmark_results_100.json', encoding='utf-8') as f:
    data = json.load(f)

print(f"Completed queries count: {len(data)}/100")
for r in data[-5:]:
    qid = r['id']
    qtext = r['query'][:35]
    cards = r['card_count']
    p4 = r['precision_at_4']
    r4 = r['recall_at_4']
    stat = "PASS" if r['task_success'] else f"FAIL ({r.get('failure_reason')})"
    print(f"  #{qid:02d}: {qtext}... | Cards: {cards} | P@4: {p4:.2f} R@4: {r4:.2f} | {stat}")
