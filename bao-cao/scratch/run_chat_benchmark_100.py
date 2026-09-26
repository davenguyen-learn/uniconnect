"""
Benchmark Runner 100 Scenarios — Đánh giá thực nghiệm RAG & Chatbot UniConnect.
Đánh giá trên Corpus 120 Hoạt động Mô phỏng có Ground Truth.

Tính toán toàn diện các metrics cho Luận văn:
1. API Availability (% HTTP 200)
2. Retrieval Precision@4
3. Retrieval Recall@4
4. Constraint Satisfaction Rate (15 câu Multi-Constraint)
5. No-Match Detection Accuracy (10 câu In-Domain No-Match)
6. Unsupported Handling Accuracy (5 câu Out-of-Domain)
7. Task Success Rate
8. Average & P95 Latency (Native vs Fallback)
9. Phân loại lỗi chi tiết (Error Categorization)

Chạy:
  python bao-cao/scratch/run_chat_benchmark_100.py
"""

import asyncio
import csv
import json
import os
import sys
import time
from datetime import datetime
import httpx

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SCRATCH_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY_PATH = os.path.join(SCRATCH_DIR, "corpus_120_registry.json")
BENCHMARK_SPEC_PATH = os.path.join(SCRATCH_DIR, "benchmark_100_ground_truth.json")
RESULTS_JSON_PATH = os.path.join(SCRATCH_DIR, "benchmark_results_100.json")
RESULTS_CSV_PATH = os.path.join(SCRATCH_DIR, "benchmark_results_100.csv")

# Load registry
with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    corpus_registry = json.load(f)

reg_by_id = {item["id"]: item for item in corpus_registry}
reg_by_slug = {item["slug"]: item for item in corpus_registry}
reg_by_title_lower = {item["title"].lower().strip(): item for item in corpus_registry}

# Load benchmark spec
with open(BENCHMARK_SPEC_PATH, "r", encoding="utf-8") as f:
    benchmark_scenarios = json.load(f)


async def get_auth_token(client: httpx.AsyncClient) -> str:
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_payload = {
        "email": "dat.nguyen@hcmut.edu.vn",
        "password": "dat123"
    }
    resp = await client.post(login_url, json=login_payload, timeout=10.0)
    if resp.status_code == 200:
        return resp.json()["access_token"]
    raise RuntimeError(f"Login failed: {resp.status_code} - {resp.text}")


def resolve_card_slug(card: dict) -> str | None:
    """Resolve an activity card back to its canonical slug."""
    act_id = card.get("activity_id") or card.get("id")
    if act_id and act_id in reg_by_id:
        return reg_by_id[act_id]["slug"]
    
    title = (card.get("title") or "").lower().strip()
    if title and title in reg_by_title_lower:
        return reg_by_title_lower[title]["slug"]

    # Fuzzy match on title substring
    for reg_title, item in reg_by_title_lower.items():
        if title in reg_title or reg_title in title:
            return item["slug"]
    return None


def check_multi_constraints(card_slug: str, constraints: dict) -> bool:
    """Verify if a returned card satisfies all explicit constraints."""
    if not card_slug or card_slug not in reg_by_slug:
        return False
    item = reg_by_slug[card_slug]

    if "campus" in constraints:
        target_campus = constraints["campus"].upper()
        if target_campus not in item["campus"].upper() and target_campus not in item["location"].upper():
            return False

    if "is_weekend" in constraints:
        if item["is_weekend"] != constraints["is_weekend"]:
            return False

    if "social_work_days_min" in constraints:
        if (item["social_work_days"] or 0.0) < constraints["social_work_days_min"]:
            return False

    if "time_of_day" in constraints:
        if item["time_of_day"].lower() != constraints["time_of_day"].lower():
            return False

    return True


async def main():
    print("=" * 95)
    print("🚀 BẮT ĐẦU CHẠY BENCHMARK 100 KỊCH BẢN ĐỘC LẬP TRÊN CORPUS 120")
    print("   Đánh giá Khoa học: Precision@4, Recall@4, Constraint Satisfaction, No-Match, Latencies")
    print("=" * 95)

    chat_url = "http://localhost:8000/api/v1/chat"
    results = []

    async with httpx.AsyncClient(timeout=40.0) as client:
        # Obtain auth token
        print("🔑 Đang đăng nhập tài khoản sinh viên dat_nguyen...")
        token = await get_auth_token(client)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        print("✅ Đăng nhập thành công! Bắt đầu thực thi 100 câu hỏi...\n")

        for idx, sc in enumerate(benchmark_scenarios, 1):
            q_id = sc["id"]
            cat = sc["category"]
            intent = sc["intent"]
            q_type = sc["query_type"]
            query = sc["query"]
            expected_slugs = sc["expected_activity_slugs"]
            constraints = sc.get("constraints", {})
            card_rule = sc["expected_card_rule"]

            t0 = time.perf_counter()
            status = 500
            data = {}
            error_msg = None

            for attempt in range(2):
                try:
                    resp = await client.post(chat_url, json={"message": query}, headers=headers)
                    elapsed = time.perf_counter() - t0
                    status = resp.status_code
                    if status == 200:
                        data = resp.json()
                        break
                    else:
                        error_msg = f"HTTP {status}: {resp.text[:100]}"
                except Exception as e:
                    elapsed = time.perf_counter() - t0
                    error_msg = str(e)
                    await asyncio.sleep(2.0)

            reply = data.get("reply", "") or (data.get("message", {}).get("content", "") if isinstance(data.get("message"), dict) else "")
            msg_obj = data.get("message") if isinstance(data.get("message"), dict) else {}
            raw_cards = msg_obj.get("cards")
            cards = raw_cards if isinstance(raw_cards, list) else []
            card_count = len(cards)

            # 1. Native vs Fallback mode
            is_gemini_native = not ("giới hạn lưu lượng" in reply or "Hệ thống đang đồng bộ" in reply or "Dưới đây là **" in reply or "Trợ lý AI tạm thời" in reply)

            # 2. Resolve returned slugs
            returned_slugs = []
            for c in cards:
                s = resolve_card_slug(c)
                if s:
                    returned_slugs.append(s)

            # 3. Card rule check
            card_rule_passed = True
            if card_rule == "MUST_HAVE" and card_count == 0:
                card_rule_passed = False
            elif card_rule == "MUST_NOT_HAVE" and card_count > 0:
                card_rule_passed = False

            # 4. Precision@4 & Recall@4
            if expected_slugs:
                matched_slugs = [s for s in returned_slugs if s in expected_slugs]
                precision_at_4 = len(matched_slugs) / min(max(len(returned_slugs), 1), 4) if returned_slugs else 0.0
                recall_at_4 = len(matched_slugs) / len(expected_slugs)
            else:
                # No expected cards (No-Match or Unsupported)
                if card_count == 0:
                    precision_at_4 = 1.0
                    recall_at_4 = 1.0
                else:
                    precision_at_4 = 0.0
                    recall_at_4 = 0.0

            # 5. Multi-constraint check
            constraint_satisfied = None
            if q_type == "MULTI_CONSTRAINT":
                constraint_satisfied = False
                for s in returned_slugs:
                    if check_multi_constraints(s, constraints):
                        constraint_satisfied = True
                        break

            # 6. In-domain No-Match check
            no_match_detected = None
            if q_type == "IN_DOMAIN_NO_MATCH":
                no_match_keywords = ["không", "chưa tìm thấy", "chưa có", "không tìm thấy", "hiện tại"]
                no_match_detected = (card_count == 0) and any(kw in reply.lower() for kw in no_match_keywords)

            # 7. Unsupported check
            unsupported_handled = None
            if q_type == "UNSUPPORTED":
                unsupported_keywords = ["không thể", "chỉ hỗ trợ", "ngoài phạm vi", "trợ lý sinh viên", "tiền ảo", "tài chính", "không có", "chưa tìm thấy"]
                unsupported_handled = (card_count == 0) and any(kw in reply.lower() for kw in unsupported_keywords)

            # 8. Task success determination
            task_success = False
            failure_reason = None

            if status != 200:
                failure_reason = "HTTP_ERROR"
            elif not card_rule_passed:
                failure_reason = "CARD_RULE_VIOLATION"
            elif q_type == "MULTI_CONSTRAINT" and not constraint_satisfied:
                failure_reason = "CONSTRAINT_UNSATISFIED"
            elif q_type == "IN_DOMAIN_NO_MATCH" and not no_match_detected:
                failure_reason = "NO_MATCH_UNRESOLVED"
            elif q_type == "UNSUPPORTED" and not unsupported_handled:
                failure_reason = "UNSUPPORTED_UNRESOLVED"
            elif expected_slugs and precision_at_4 == 0.0:
                failure_reason = "RELEVANCE_MISMATCH"
            else:
                task_success = True

            result_entry = {
                "id": q_id,
                "category": cat,
                "intent": intent,
                "query_type": q_type,
                "query": query,
                "status_code": status,
                "latency_sec": round(elapsed, 3),
                "is_gemini_native": is_gemini_native,
                "card_count": card_count,
                "card_titles": [c.get("title") for c in cards if isinstance(c, dict) and c.get("title")] if cards else [],
                "returned_slugs": returned_slugs,
                "expected_slugs": expected_slugs,
                "precision_at_4": round(precision_at_4, 3),
                "recall_at_4": round(recall_at_4, 3),
                "card_rule_passed": card_rule_passed,
                "constraint_satisfied": constraint_satisfied,
                "no_match_detected": no_match_detected,
                "unsupported_handled": unsupported_handled,
                "task_success": task_success,
                "failure_reason": failure_reason,
                "full_reply": reply,
            }
            results.append(result_entry)

            # Incremental save
            with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f_inc:
                json.dump(results, f_inc, ensure_ascii=False, indent=2)

            mode_str = "Native" if is_gemini_native else "Fallback"
            stat_str = "✅ PASS" if task_success else f"❌ FAIL ({failure_reason})"
            print(f"[{q_id:03d}/100] [{q_type[:15]:15}] {elapsed:.2f}s ({mode_str:8}) | Cards: {card_count} | P@4: {precision_at_4:.2f} R@4: {recall_at_4:.2f} | {stat_str} | {query[:35]}...")

            # Pacing between queries
            await asyncio.sleep(3.5)

    # Save final CSV and JSON
    with open(RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    csv_fields = [
        "id", "category", "intent", "query_type", "query", "status_code",
        "latency_sec", "is_gemini_native", "card_count", "precision_at_4",
        "recall_at_4", "card_rule_passed", "constraint_satisfied",
        "no_match_detected", "unsupported_handled", "task_success", "failure_reason"
    ]
    with open(RESULTS_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    # Calculate overall metrics
    total_q = len(results)
    http_200_count = sum(1 for r in results if r["status_code"] == 200)
    task_success_count = sum(1 for r in results if r["task_success"])
    native_count = sum(1 for r in results if r["is_gemini_native"])
    fallback_count = total_q - native_count

    # Retrieval metrics on queries with expected slugs (60 queries)
    retrieval_queries = [r for r in results if r["expected_slugs"]]
    avg_precision_at_4 = sum(r["precision_at_4"] for r in retrieval_queries) / len(retrieval_queries) if retrieval_queries else 0.0
    avg_recall_at_4 = sum(r["recall_at_4"] for r in retrieval_queries) / len(retrieval_queries) if retrieval_queries else 0.0

    # Constraint satisfaction (15 queries)
    multi_const_queries = [r for r in results if r["query_type"] == "MULTI_CONSTRAINT"]
    constraint_pass_count = sum(1 for r in multi_const_queries if r["constraint_satisfied"])
    constraint_rate = (constraint_pass_count / len(multi_const_queries)) * 100 if multi_const_queries else 0.0

    # No-match accuracy (10 queries)
    no_match_queries = [r for r in results if r["query_type"] == "IN_DOMAIN_NO_MATCH"]
    no_match_pass_count = sum(1 for r in no_match_queries if r["no_match_detected"])
    no_match_accuracy = (no_match_pass_count / len(no_match_queries)) * 100 if no_match_queries else 0.0

    # Unsupported accuracy (5 queries)
    unsupported_queries = [r for r in results if r["query_type"] == "UNSUPPORTED"]
    unsupported_pass_count = sum(1 for r in unsupported_queries if r["unsupported_handled"])
    unsupported_accuracy = (unsupported_pass_count / len(unsupported_queries)) * 100 if unsupported_queries else 0.0

    # Latencies
    native_latencies = [r["latency_sec"] for r in results if r["is_gemini_native"]]
    fallback_latencies = [r["latency_sec"] for r in results if not r["is_gemini_native"]]
    all_latencies = sorted(r["latency_sec"] for r in results)

    avg_latency = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0
    # Nearest-rank 95th percentile: for N=100, rank is 95, corresponding to index 94 in 0-indexed sorted array
    p95_index = max(0, int(0.95 * len(all_latencies)) - 1) if len(all_latencies) == 100 else int(0.95 * len(all_latencies))
    p95_latency = all_latencies[p95_index] if all_latencies else 0.0
    avg_native_lat = sum(native_latencies) / len(native_latencies) if native_latencies else 0.0
    avg_fallback_lat = sum(fallback_latencies) / len(fallback_latencies) if fallback_latencies else 0.0

    # Failure category breakdown
    failure_breakdown = {}
    for r in results:
        if not r["task_success"]:
            rs = r["failure_reason"] or "UNKNOWN"
            failure_breakdown[rs] = failure_breakdown.get(rs, 0) + 1

    print("\n" + "=" * 95)
    print("📊 BÁO CÁO KẾT QUẢ THỰC NGHIỆM ĐÁNH GIÁ CHATBOT & RAG (100 KỊCH BẢN CHUẨN HÓA)")
    print("=" * 95)
    print(f"• Tổng số truy vấn kiểm thử (Requests):      {total_q}")
    print(f"• Tính sẵn sàng hệ thống (HTTP 200 Avail):   {http_200_count}/{total_q} ({(http_200_count/total_q)*100:.1f}%)")
    print(f"• Tỷ lệ xử lý Native Gemini LLM:             {native_count}/{total_q} ({(native_count/total_q)*100:.1f}%)")
    print(f"• Tỷ lệ xử lý Deterministic Fallback:        {fallback_count}/{total_q} ({(fallback_count/total_q)*100:.1f}%)")
    print("-" * 95)
    print(f"🎯 CHỈ SỐ TRUY HỒI NGỮ NGHĨA (RAG RETRIEVAL METRICS):")
    print(f"• Average Precision@4 (Top-4 Relevant):      {avg_precision_at_4*100:.1f}%")
    print(f"• Average Recall@4 (Coverage of Relevant):   {avg_recall_at_4*100:.1f}%")
    print(f"• Constraint Satisfaction Rate:              {constraint_pass_count}/{len(multi_const_queries)} ({constraint_rate:.1f}%)")
    print(f"• In-domain No-Match Detection Accuracy:     {no_match_pass_count}/{len(no_match_queries)} ({no_match_accuracy:.1f}%)")
    print(f"• Unsupported / Out-of-Domain Accuracy:      {unsupported_pass_count}/{len(unsupported_queries)} ({unsupported_accuracy:.1f}%)")
    print(f"• Task Success Rate (End-to-End Success):    {task_success_count}/{total_q} ({(task_success_count/total_q)*100:.1f}%)")
    print("-" * 95)
    print(f"⚡ HIỆU NĂNG THỜI GIAN ĐÁP ỨNG (LATENCY METRICS):")
    print(f"• Thời gian phản hồi trung bình (Average):   {avg_latency:.3f} s")
    print(f"• Thời gian phản hồi P95 (95th Percentile):  {p95_latency:.3f} s")
    print(f"• Độ trễ Native Gemini:                      {avg_native_lat:.3f} s")
    print(f"• Độ trễ Deterministic Fallback:             {avg_fallback_lat:.3f} s")
    print("-" * 95)
    print(f"🔍 PHÂN LOẠI NGUYÊN NHÂN LỖI (ERROR ANALYSIS):")
    if failure_breakdown:
        for reason, cnt in failure_breakdown.items():
            print(f"• {reason}: {cnt} ca ({(cnt/total_q)*100:.1f}%)")
    else:
        print("• Không ghi nhận lỗi kỹ thuật nào.")
    print("=" * 95)

if __name__ == "__main__":
    asyncio.run(main())
