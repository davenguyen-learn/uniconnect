import re
import json
import csv
import os

log_path = r"C:\Users\Admin\.gemini\antigravity-ide\brain\72b52ba5-b977-4fe7-8b4a-dc5ebbe146c0\.system_generated\tasks\task-4288.log"
with open(log_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

records = []
pattern = re.compile(r"\[(\d+)/50\]\s+\[(.*?)\]\s+([\d\.]+)s\s+\((Native|Fallback)\)\s+\|\s+Cards:\s+(\d+)\s+\(Rule:\s+(.*?)\)\s+\|\s+Task:\s+(PASS|FAIL)\s+\|\s+Q:\s+(.*)")

cat_map = {
    "Học thuật": "Học thuật & Kỹ năng",
    "Tình nguyệ": "Tình nguyện & CTXH",
    "Thể thao &": "Thể thao & Giải trí",
    "Lịch bận &": "Lịch bận & Xung đột",
    "CLB & Quy": "CLB & Quy chế & An toàn",
}

for line in lines:
    m = pattern.search(line)
    if m:
        qid = int(m.group(1))
        cat_short = m.group(2).strip()
        lat = float(m.group(3))
        mode = m.group(4)
        cards = int(m.group(5))
        rule = m.group(6)
        task = m.group(7)
        q_preview = m.group(8).strip()

        full_cat = cat_map.get(cat_short, cat_short)

        records.append({
            "id": qid,
            "category": full_cat,
            "latency_sec": lat,
            "is_gemini_native": (mode == "Native"),
            "card_count": cards,
            "card_rule": rule,
            "card_rule_passed": not ((rule == "MUST_HAVE" and cards == 0) or (rule == "MUST_NOT_HAVE" and cards > 0)),
            "task_success": (task == "PASS"),
            "query_preview": q_preview,
        })

print(f"Parsed {len(records)} benchmark records successfully.")

out_dir = r"c:\Users\Admin\Code\uniconnect-v2\bao-cao\scratch"
with open(os.path.join(out_dir, "benchmark_results_50.json"), "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

with open(os.path.join(out_dir, "benchmark_results_50.csv"), "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)

# Stats calculation
cat_stats = {}
for r in records:
    c = r["category"]
    if c not in cat_stats:
        cat_stats[c] = {"total": 0, "native": 0, "fallback": 0, "pass": 0, "card_ok": 0, "lat_native": [], "lat_fallback": []}
    s = cat_stats[c]
    s["total"] += 1
    if r["is_gemini_native"]:
        s["native"] += 1
        s["lat_native"].append(r["latency_sec"])
    else:
        s["fallback"] += 1
        s["lat_fallback"].append(r["latency_sec"])
    if r["task_success"]:
        s["pass"] += 1
    if r["card_rule_passed"]:
        s["card_ok"] += 1

print("\n" + "=" * 98)
print("BẢNG TỔNG HỢP ĐÁNH GIÁ THỰC NGHIỆM ĐỘC LẬP CHATBOT (50 KỊCH BẢN)")
print("=" * 98)
print(f"{'Nhóm nghiệp vụ':<26} | {'Tổng':<4} | {'Native':<6} | {'Fallback':<8} | {'Card Match':<10} | {'Task Success':<12} | {'Lat. Native':<11} | {'Lat. Fallback':<13}")
print("-" * 98)

tot_n = len(records)
tot_nat = sum(s["native"] for s in cat_stats.values())
tot_fb = sum(s["fallback"] for s in cat_stats.values())
tot_pass = sum(s["pass"] for s in cat_stats.values())
tot_card = sum(s["card_ok"] for s in cat_stats.values())
all_lat_nat = [lat for s in cat_stats.values() for lat in s["lat_native"]]
all_lat_fb = [lat for s in cat_stats.values() for lat in s["lat_fallback"]]

for cat, s in cat_stats.items():
    n = s["total"]
    nat = s["native"]
    fb = s["fallback"]
    card_pct = (s["card_ok"] / n) * 100
    pass_pct = (s["pass"] / n) * 100
    avg_nat = (sum(s["lat_native"]) / nat) if nat > 0 else 0.0
    avg_fb = (sum(s["lat_fallback"]) / fb) if fb > 0 else 0.0
    print(f"{cat:<26} | {n:<4} | {nat:<6} | {fb:<8} | {card_pct:>8.1f}% | {pass_pct:>10.1f}% | {avg_nat:>9.2f}s | {avg_fb:>11.2f}s")

print("-" * 98)
tot_card_pct = (tot_card / tot_n) * 100
tot_pass_pct = (tot_pass / tot_n) * 100
avg_tot_nat = (sum(all_lat_nat) / tot_nat) if tot_nat > 0 else 0.0
avg_tot_fb = (sum(all_lat_fb) / tot_fb) if tot_fb > 0 else 0.0
print(f"{'TOÀN BỘ HỆ THỐNG':<26} | {tot_n:<4} | {tot_nat:<6} | {tot_fb:<8} | {tot_card_pct:>8.1f}% | {tot_pass_pct:>10.1f}% | {avg_tot_nat:>9.2f}s | {avg_tot_fb:>11.2f}s")
print("=" * 98)
