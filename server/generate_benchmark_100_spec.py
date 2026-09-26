"""
Script tạo bộ Benchmark 100 câu hỏi độc lập kèm Ground Truth Schema chi tiết cho UniConnect.
Tuân thủ tuyệt đối cấu trúc 7 nhóm:
- 40 Direct Retrieval
- 20 Semantic Paraphrase
- 15 Multi-Constraint Retrieval
- 10 In-Domain No-Match
- 5 Schedule & Conflict
- 5 Group & Policy
- 5 Unsupported / Out-of-Domain
Tổng cộng: 100 câu hỏi.
"""

import json
import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

scratch_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bao-cao", "scratch")
registry_path = os.path.join(scratch_dir, "corpus_120_registry.json")
out_path = os.path.join(scratch_dir, "benchmark_100_ground_truth.json")

with open(registry_path, "r", encoding="utf-8") as f:
    registry = json.load(f)

# Map slug to registry item for quick lookup
reg_by_slug = {item["slug"]: item for item in registry}

BENCHMARK_100 = [
    # =========================================================================
    # NHÓM 1: DIRECT RETRIEVAL (40 câu)
    # =========================================================================
    # Công nghệ & Kỹ thuật (1-10)
    {
        "id": 1, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm workshop học về Machine Learning cơ bản và Scikit-Learn.",
        "expected_activity_slugs": ["tech_ai_ml_fundamentals"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 2, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có chuyên đề nào dạy Deep Learning và PyTorch không?",
        "expected_activity_slugs": ["tech_ai_deep_learning_pytorch"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 3, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm seminar về thị giác máy tính Computer Vision và xử lý ảnh OpenCV.",
        "expected_activity_slugs": ["tech_ai_computer_vision_opencv"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 4, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có buổi hướng dẫn nào về Generative AI và xây dựng hệ thống RAG không?",
        "expected_activity_slugs": ["tech_ai_genai_llm_rag"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 5, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm workshop thực hành đóng gói ứng dụng với Docker và Docker Compose.",
        "expected_activity_slugs": ["tech_infra_docker_containerization"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 6, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có seminar chuyên sâu về điều phối container bằng Kubernetes không?",
        "expected_activity_slugs": ["tech_infra_kubernetes_cluster"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 7, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm khóa học về điện toán đám mây Amazon Web Services AWS.",
        "expected_activity_slugs": ["tech_infra_aws_cloud_practitioner"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 8, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có buổi tọa đàm nào về tự động hóa CI/CD với GitHub Actions không?",
        "expected_activity_slugs": ["tech_infra_devops_cicd_github_actions"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 9, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm seminar về kiểm thử xâm nhập Pentest và các lỗ hổng web OWASP Top 10.",
        "expected_activity_slugs": ["tech_sec_owasp_pentest_web"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 10, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Thông tin về cuộc thi Bách Khoa Hackathon 2026 AI for Smart Campus.",
        "expected_activity_slugs": ["tech_hackathon_smart_campus_2026"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },

    # Học thuật & Ôn thi (11-18)
    {
        "id": 11, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm lớp ôn tập thi giữa kỳ môn Giải tích 1.",
        "expected_activity_slugs": ["acad_math_calculus_1_midterm"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 12, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có nhóm ôn thi cuối kỳ môn Giải tích 2 tích phân bội không?",
        "expected_activity_slugs": ["acad_math_calculus_2_finals"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 13, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm buổi gia sư phụ đạo môn Đại số tuyến tính không gian vector.",
        "expected_activity_slugs": ["acad_math_linear_algebra_matrices"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 14, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có nhóm tự học môn Xác suất Thống kê kiểm định giả thuyết không?",
        "expected_activity_slugs": ["acad_math_probability_statistics"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 15, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm chuyên đề ôn tập môn Vật lý 1 cơ học vật rắn.",
        "expected_activity_slugs": ["acad_phys_physics_1_mechanics"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 16, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có buổi học nhóm môn Cấu trúc Dữ liệu và Giải thuật DSA ở thư viện không?",
        "expected_activity_slugs": ["acad_cs_dsa_data_structures_library"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 17, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm workshop học về Lập trình hướng đối tượng OOP và Design Patterns.",
        "expected_activity_slugs": ["acad_cs_oop_cpp_design_patterns"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 18, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có seminar về Hệ điều hành Operating Systems và xử lý bế tắc Deadlock không?",
        "expected_activity_slugs": ["acad_cs_os_operating_systems_concurrency"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },

    # Tình nguyện & CTXH (19-25)
    {
        "id": 19, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm hoạt động Chiến dịch Tình nguyện Ngày Chủ Nhật Xanh vệ sinh Hồ Tiền Phong.",
        "expected_activity_slugs": ["vol_ctxh_sunday_green_lake_cleanup"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 20, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Thông tin về Ngày hội Hiến máu Nhân đạo Giọt hồng Bách Khoa.",
        "expected_activity_slugs": ["vol_ctxh_blood_donation_spring_2026", "vol_ctxh_blood_donor_care_team"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 21, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có hoạt động Tiếp sức Mùa thi hỗ trợ thí sinh THPT không?",
        "expected_activity_slugs": ["vol_ctxh_exam_support_tiep_suc_mua_thi"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 22, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm hoạt động Đổi Pin cũ và Rác thải Điện tử lấy Cây Sen đá.",
        "expected_activity_slugs": ["vol_ctxh_ewaste_battery_recycle"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 23, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có hoạt động Gia sư Áo xanh dạy học cho trẻ em mái ấm không?",
        "expected_activity_slugs": ["vol_ctxh_green_tutor_shelter_children"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 24, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm đội hình hỗ trợ Tân Sinh viên K26 làm thủ tục nhập học.",
        "expected_activity_slugs": ["vol_ctxh_freshmen_welcome_support"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 25, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm hoạt động vệ sinh phòng đọc thư viện và sắp xếp giá sách A2.",
        "expected_activity_slugs": ["vol_ctxh_library_book_arrangement_cs1"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },

    # Thể thao & Giải trí (26-32)
    {
        "id": 26, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có kèo đá bóng sân 7 tối thứ Năm tại KTX Bách Khoa không?",
        "expected_activity_slugs": ["sport_football_thu_night_7v7"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 27, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm kèo giao lưu bóng đá mini sân 5 chiều thứ Bảy ở Làng Đại học.",
        "expected_activity_slugs": ["sport_football_sat_afternoon_5v5"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 28, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có buổi giao lưu đánh cầu lông ở sân C3 Bách Khoa CS1 không?",
        "expected_activity_slugs": ["sport_badminton_c3_courts_weekend"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 29, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm kèo ném bóng rổ ngoài trời giao lưu ở Bách Khoa CS1.",
        "expected_activity_slugs": ["sport_basketball_weekend_outdoor_cs1"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 30, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có hoạt động chạy bộ rèn luyện sức bền sáng sớm quanh hồ KTX ĐHQG không?",
        "expected_activity_slugs": ["sport_running_morning_lake_ktx_cs2"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 31, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm buổi sinh hoạt CLB Cờ vua và Cờ tướng ở sảnh nhà H6 CS2.",
        "expected_activity_slugs": ["sport_chess_xiangqi_h6_lobby_cs2"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 32, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có lớp bơi lội rèn luyện thể lực cuối tuần ở hồ bơi Phú Thọ không?",
        "expected_activity_slugs": ["sport_swimming_weekend_swimmingpool_cs1"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },

    # CLB, Hướng nghiệp & Kỹ năng (33-40)
    {
        "id": 33, "category": "CLB & Đội nhóm", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Đêm nhạc Acoustic của CLB Guitar BGC Bách Khoa diễn ra ở đâu?",
        "expected_activity_slugs": ["club_music_guitar_bgc_acoustic_night"],
        "constraints": {"category": "CLB & Đội nhóm"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 34, "category": "CLB & Đội nhóm", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Thông tin buổi Coffee Talk bằng tiếng Anh của CLB Tiếng Anh BEC.",
        "expected_activity_slugs": ["club_lang_bec_english_coffee_talk_ai"],
        "constraints": {"category": "CLB & Đội nhóm"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 35, "category": "CLB & Đội nhóm", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có buổi trình diễn robot và tuyển thành viên của Đội Robocon không?",
        "expected_activity_slugs": ["club_robotics_robocon_recruitment_demo"],
        "constraints": {"category": "CLB & Đội nhóm"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 36, "category": "Hướng nghiệp & Việc làm", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Khi nào diễn ra Ngày hội Việc làm Bách Khoa Job Fair 2026?",
        "expected_activity_slugs": ["career_job_fair_bachkhoa_annual_2026"],
        "constraints": {"category": "Hướng nghiệp & Việc làm"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 37, "category": "Hướng nghiệp & Việc làm", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm workshop hướng dẫn viết CV công nghệ và sửa CV xin việc IT.",
        "expected_activity_slugs": ["career_cv_workshop_tech_hr_review"],
        "constraints": {"category": "Hướng nghiệp & Việc làm"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 38, "category": "Hướng nghiệp & Việc làm", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có chương trình phỏng vấn thử Mock Interview 1-1 với Senior Tech Lead không?",
        "expected_activity_slugs": ["career_mock_interview_senior_leads"],
        "constraints": {"category": "Hướng nghiệp & Việc làm"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 39, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Tìm lớp huấn luyện kỹ năng thuyết trình tự tin và thiết kế slide báo cáo.",
        "expected_activity_slugs": ["soft_public_speaking_presentation_skills"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 40, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "DIRECT_RETRIEVAL",
        "query": "Có workshop nào dạy kỹ thuật quản lý thời gian và chống trì hoãn Pomodoro không?",
        "expected_activity_slugs": ["soft_time_management_pomodoro_productivity"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },

    # =========================================================================
    # NHÓM 2: SEMANTIC PARAPHRASE (20 câu)
    # =========================================================================
    {
        "id": 41, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Có hoạt động nào dạy cách đóng gói và triển khai ứng dụng bằng container không?",
        "expected_activity_slugs": ["tech_infra_docker_containerization", "tech_infra_kubernetes_cluster"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 42, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Tôi muốn học cách huấn luyện mô hình mạng nơ-ron nhân tạo nhận diện đồ vật.",
        "expected_activity_slugs": ["tech_ai_deep_learning_pytorch", "tech_ai_computer_vision_opencv"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 43, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Có chỗ nào hướng dẫn xây dựng chatbot thông minh trả lời theo tài liệu riêng không?",
        "expected_activity_slugs": ["tech_ai_genai_llm_rag"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 44, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Làm sao để tự động chạy test và đưa code lên server khi commit GitHub?",
        "expected_activity_slugs": ["tech_infra_devops_cicd_github_actions"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 45, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Có lớp nào hướng dẫn tấn công thử nghiệm web để biết cách bảo mật không?",
        "expected_activity_slugs": ["tech_sec_owasp_pentest_web"],
        "constraints": {"category": "Công nghệ & Kỹ thuật"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 46, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Em bị mất gốc phần tính tích phân suy rộng và chuỗi số, có ai kèm không ạ?",
        "expected_activity_slugs": ["acad_math_calculus_1_midterm"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 47, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Có bạn nào đang cày bài tập cây nhị phân và đồ thị môn thuật toán ở thư viện không?",
        "expected_activity_slugs": ["acad_cs_dsa_data_structures_library", "acad_cs_dsa_leetcode_competitive_programming"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 48, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Tôi đang tìm hiểu cách viết báo cáo luận văn có công thức toán đẹp mắt.",
        "expected_activity_slugs": ["acad_skills_academic_writing_latex"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 49, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Cách đăng ký thi NCKH sinh viên và xin kinh phí đề tài nghiên cứu thế nào?",
        "expected_activity_slugs": ["acad_research_scientific_paper_writing"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 50, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Có buổi luyện nói tiếng Anh giao tiếp nào về các chủ đề công nghệ hiện đại không?",
        "expected_activity_slugs": ["club_lang_bec_english_coffee_talk_ai", "acad_lang_ielts_speaking_band_7"],
        "constraints": {},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 51, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Có chương trình nào vớt rác và bảo vệ môi trường nước quanh ký túc xá không?",
        "expected_activity_slugs": ["vol_ctxh_sunday_green_lake_cleanup"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 52, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Tôi có mấy đồ linh kiện điện tử và pin hỏng, có chỗ nào nhận gom đổi quà không?",
        "expected_activity_slugs": ["vol_ctxh_ewaste_battery_recycle"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 53, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Muốn tham gia dạy chữ và kèm học tập cho các bé mồ côi thì đăng ký ở đâu?",
        "expected_activity_slugs": ["vol_ctxh_green_tutor_shelter_children"],
        "constraints": {"category": "Tình nguyện & CTXH"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 54, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Có kèo bóng đá phủi nào buổi tối sau giờ tan ca học quanh trường không?",
        "expected_activity_slugs": ["sport_football_thu_night_7v7", "sport_football_futsal_indoor_cs1"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 55, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Tìm người chơi bóng bàn đánh đơn hoặc đánh đôi rèn luyện phản xạ.",
        "expected_activity_slugs": ["sport_tabletennis_pingpong_cs1"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 56, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Có chỗ nào giao lưu cờ thế, đánh cờ chớp giao hữu giữa các sinh viên không?",
        "expected_activity_slugs": ["sport_chess_xiangqi_h6_lobby_cs2"],
        "constraints": {"category": "Thể thao & Giải trí"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 57, "category": "CLB & Đội nhóm", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Tối thứ Sáu rảnh muốn nghe đàn hát acoustic nhẹ nhàng thì ghé đâu?",
        "expected_activity_slugs": ["club_music_guitar_bgc_acoustic_night"],
        "constraints": {"category": "CLB & Đội nhóm"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 58, "category": "Hướng nghiệp & Việc làm", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Làm sao để chuẩn bị hồ sơ ứng tuyển IT không bị loại từ vòng lọc tự động ATS?",
        "expected_activity_slugs": ["career_cv_workshop_tech_hr_review"],
        "constraints": {"category": "Hướng nghiệp & Việc làm"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 59, "category": "Hướng nghiệp & Việc làm", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Có cơ hội nào được phỏng vấn thử coding trực tiếp với các chuyên gia công nghệ không?",
        "expected_activity_slugs": ["career_mock_interview_senior_leads"],
        "constraints": {"category": "Hướng nghiệp & Việc làm"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 60, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "SEMANTIC_PARAPHRASE",
        "query": "Nhóm làm bài tập lớn hay cãi nhau bất đồng ý kiến thì xử lý thế nào cho khéo?",
        "expected_activity_slugs": ["soft_conflict_resolution_teamwork_skills"],
        "constraints": {"category": "Học thuật & Kỹ năng"},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },

    # =========================================================================
    # NHÓM 3: MULTI-CONSTRAINT RETRIEVAL (15 câu)
    # =========================================================================
    {
        "id": 61, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Tìm hoạt động tình nguyện cuối tuần ở Cơ sở 2 có điểm CTXH.",
        "expected_activity_slugs": ["vol_ctxh_sunday_green_lake_cleanup", "vol_ctxh_dorm_ktx_cleanup_cs2"],
        "constraints": {
            "category": "Tình nguyện & CTXH",
            "campus": "CS2",
            "is_weekend": True,
            "social_work_days_min": 0.5
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 62, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Có hoạt động tình nguyện nào ở CS1 được cộng từ 1 ngày CTXH trở lên không?",
        "expected_activity_slugs": ["vol_ctxh_blood_donation_spring_2026", "vol_ctxh_exam_support_tiep_suc_mua_thi", "vol_ctxh_freshmen_welcome_support", "vol_ctxh_paint_dorm_benches_cs1"],
        "constraints": {
            "category": "Tình nguyện & CTXH",
            "campus": "CS1",
            "social_work_days_min": 1.0
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 63, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Tìm trận đá bóng sân 7 buổi tối ở Cơ sở 1.",
        "expected_activity_slugs": ["sport_football_thu_night_7v7"],
        "constraints": {
            "category": "Thể thao & Giải trí",
            "campus": "CS1",
            "time_of_day": "evening"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 64, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Có hoạt động chạy bộ sáng sớm ở Cơ sở 2 Dĩ An không?",
        "expected_activity_slugs": ["sport_running_morning_lake_ktx_cs2"],
        "constraints": {
            "category": "Thể thao & Giải trí",
            "campus": "CS2",
            "time_of_day": "morning"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 65, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Tìm workshop về trí tuệ nhân tạo hoặc deep learning diễn ra ở Cơ sở 2 Dĩ An.",
        "expected_activity_slugs": ["tech_ai_deep_learning_pytorch", "tech_ai_data_science_eda"],
        "constraints": {
            "category": "Công nghệ & Kỹ thuật",
            "campus": "CS2"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 66, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Có seminar công nghệ nào diễn ra vào buổi tối ở Cơ sở 1 không?",
        "expected_activity_slugs": ["tech_ai_genai_llm_rag", "tech_infra_devops_cicd_github_actions", "tech_database_sql_optimization_indexes"],
        "constraints": {
            "category": "Công nghệ & Kỹ thuật",
            "campus": "CS1",
            "time_of_day": "evening"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 67, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Tìm lớp ôn thi toán Giải tích 1 vào buổi sáng ở Cơ sở 1.",
        "expected_activity_slugs": ["acad_math_calculus_1_midterm"],
        "constraints": {
            "category": "Học thuật & Kỹ năng",
            "campus": "CS1",
            "time_of_day": "morning"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 68, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Có lớp ôn thi toán Giải tích 2 ở Cơ sở 2 Dĩ An không?",
        "expected_activity_slugs": ["acad_math_calculus_2_finals"],
        "constraints": {
            "category": "Học thuật & Kỹ năng",
            "campus": "CS2"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 69, "category": "CLB & Đội nhóm", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Tìm buổi sinh hoạt văn nghệ acoustic vào buổi tối ở Cơ sở 1.",
        "expected_activity_slugs": ["club_music_guitar_bgc_acoustic_night"],
        "constraints": {
            "category": "CLB & Đội nhóm",
            "campus": "CS1",
            "time_of_day": "evening"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 70, "category": "Hướng nghiệp & Việc làm", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Có sự kiện tuyển dụng hoặc gặp gỡ doanh nghiệp công nghệ tại Cơ sở 2 Dĩ An không?",
        "expected_activity_slugs": ["career_internship_bosch_automotive_talk", "career_scholarship_erasmus_postgraduate"],
        "constraints": {
            "category": "Hướng nghiệp & Việc làm",
            "campus": "CS2"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 71, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Tìm hoạt động bóng rổ diễn ra vào cuối tuần ở Cơ sở 1.",
        "expected_activity_slugs": ["sport_basketball_weekend_outdoor_cs1"],
        "constraints": {
            "category": "Thể thao & Giải trí",
            "campus": "CS1",
            "is_weekend": True
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 72, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Tìm hoạt động tình nguyện đổi pin cũ lấy quà bảo vệ môi trường ở Cơ sở 1.",
        "expected_activity_slugs": ["vol_ctxh_ewaste_battery_recycle"],
        "constraints": {
            "category": "Tình nguyện & CTXH",
            "campus": "CS1"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 73, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Có kèo chơi cờ vua cờ tướng vào buổi chiều ở Cơ sở 2 không?",
        "expected_activity_slugs": ["sport_chess_xiangqi_h6_lobby_cs2"],
        "constraints": {
            "category": "Thể thao & Giải trí",
            "campus": "CS2",
            "time_of_day": "afternoon"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 74, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Tìm workshop học về Linux và máy chủ web Nginx tại Cơ sở 2 Dĩ An.",
        "expected_activity_slugs": ["tech_infra_linux_server_admin"],
        "constraints": {
            "category": "Công nghệ & Kỹ thuật",
            "campus": "CS2"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },
    {
        "id": 75, "category": "Hướng nghiệp & Việc làm", "intent": "ACTIVITY_SEARCH",
        "query_type": "MULTI_CONSTRAINT",
        "query": "Tìm sự kiện ngày hội việc làm quy mô lớn vào ban ngày ở Cơ sở 1.",
        "expected_activity_slugs": ["career_job_fair_bachkhoa_annual_2026"],
        "constraints": {
            "category": "Hướng nghiệp & Việc làm",
            "campus": "CS1"
        },
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },

    # =========================================================================
    # NHÓM 4: IN-DOMAIN NO-MATCH (10 câu)
    # =========================================================================
    {
        "id": 76, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Có giải thi đấu bóng rổ 3x3 lúc 23h đêm tại Cơ sở 2 không?",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 77, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Tìm câu lạc bộ bắn cung thể thao hoặc lớp học bắn cung tại Bách Khoa CS1.",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 78, "category": "Công nghệ & Kỹ thuật", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Có workshop nào về thiết kế chip quang học photonics và máy tính lượng tử không?",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 79, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Có lớp dạy kèm tiếng Nga hoặc tiếng Ả Rập tại khuôn viên trường không?",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 80, "category": "Tình nguyện & CTXH", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Tìm hoạt động tình nguyện cứu trợ thú cưng mèo hoang quanh cơ sở 1 được cấp ngày CTXH.",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 81, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Có giải thi đấu cờ ca-rô ăn tiền thưởng 10 triệu đồng tại trường không?",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 82, "category": "CLB & Đội nhóm", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Tìm câu lạc bộ mô tô phân khối lớn hoặc phượt xe cào cào của trường.",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 83, "category": "Hướng nghiệp & Việc làm", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Có hội thảo tuyển dụng phi công và tiếp viên hàng không tại Hội trường A5 không?",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 84, "category": "Học thuật & Kỹ năng", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Tìm khóa học trực tiếp về lập trình ngôn ngữ COBOL và máy chủ Mainframe IBM.",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 85, "category": "Thể thao & Giải trí", "intent": "ACTIVITY_SEARCH",
        "query_type": "IN_DOMAIN_NO_MATCH",
        "query": "Có giải bóng đá 11 người chuyên nghiệp thi đấu lúc 4 giờ sáng không?",
        "expected_activity_slugs": [],
        "constraints": {"is_match": False},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },

    # =========================================================================
    # NHÓM 5: SCHEDULE & CONFLICT CHECK (5 câu)
    # =========================================================================
    {
        "id": 86, "category": "Lịch học & Xung đột", "intent": "GET_SCHEDULE",
        "query_type": "SCHEDULE_CONFLICT",
        "query": "Xem thời khóa biểu và các khung giờ học bận trong tuần này của tôi.",
        "expected_activity_slugs": [],
        "constraints": {"intent": "get_user_schedule"},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 87, "category": "Lịch học & Xung đột", "intent": "GET_SCHEDULE",
        "query_type": "SCHEDULE_CONFLICT",
        "query": "Sáng thứ Hai tôi có bị kẹt lịch học hay bận môn gì không?",
        "expected_activity_slugs": [],
        "constraints": {"day_of_week": 0, "intent": "get_user_schedule"},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 88, "category": "Lịch học & Xung đột", "intent": "GET_SCHEDULE",
        "query_type": "SCHEDULE_CONFLICT",
        "query": "Chiều thứ Ba tôi có tiết học nào trên lớp không?",
        "expected_activity_slugs": [],
        "constraints": {"day_of_week": 1, "intent": "get_user_schedule"},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 89, "category": "Lịch học & Xung đột", "intent": "GET_SCHEDULE",
        "query_type": "SCHEDULE_CONFLICT",
        "query": "Sáng thứ Sáu tôi học ở cơ sở nào và mấy giờ bắt đầu?",
        "expected_activity_slugs": [],
        "constraints": {"day_of_week": 4, "intent": "get_user_schedule"},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 90, "category": "Lịch học & Xung đột", "intent": "ACTIVITY_SEARCH",
        "query_type": "SCHEDULE_CONFLICT",
        "query": "Tìm hoạt động học tập nào diễn ra vào khung giờ tôi hoàn toàn rảnh rỗi.",
        "expected_activity_slugs": ["tech_ai_ml_fundamentals", "tech_infra_devops_cicd_github_actions"],
        "constraints": {"conflict_free": True},
        "expected_card_rule": "MUST_HAVE", "min_expected_cards": 1, "max_expected_cards": 4
    },

    # =========================================================================
    # NHÓM 6: GROUP & POLICY INFO (5 câu)
    # =========================================================================
    {
        "id": 91, "category": "CLB & Chính sách", "intent": "GET_GROUP_INFO",
        "query_type": "GROUP_POLICY",
        "query": "Tìm các câu lạc bộ học thuật và lập trình hiện có trong trường.",
        "expected_activity_slugs": [],
        "constraints": {"intent": "search_groups"},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 92, "category": "CLB & Chính sách", "intent": "GET_GROUP_INFO",
        "query_type": "GROUP_POLICY",
        "query": "Trong trường có câu lạc bộ tiếng Anh hoặc câu lạc bộ guitar nào không?",
        "expected_activity_slugs": [],
        "constraints": {"intent": "search_groups"},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 93, "category": "CLB & Chính sách", "intent": "GET_POLICY_INFO",
        "query_type": "GROUP_POLICY",
        "query": "Sinh viên cần hoàn thành bao nhiêu ngày Công tác Xã hội để đủ điều kiện xét tốt nghiệp?",
        "expected_activity_slugs": [],
        "constraints": {"topic": "ctxh_policy"},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 94, "category": "CLB & Chính sách", "intent": "GET_POLICY_INFO",
        "query_type": "GROUP_POLICY",
        "query": "Quy định về việc cộng điểm rèn luyện khi tham gia các hoạt động phong trào ra sao?",
        "expected_activity_slugs": [],
        "constraints": {"topic": "drl_policy"},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 95, "category": "CLB & Chính sách", "intent": "GET_POLICY_INFO",
        "query_type": "GROUP_POLICY",
        "query": "Làm thế nào để tạo một nhóm hoặc câu lạc bộ mới trên hệ thống UniConnect?",
        "expected_activity_slugs": [],
        "constraints": {"topic": "group_creation_policy"},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },

    # =========================================================================
    # NHÓM 7: UNSUPPORTED / OUT-OF-DOMAIN (5 câu)
    # =========================================================================
    {
        "id": 96, "category": "Ngoài phạm vi", "intent": "UNSUPPORTED",
        "query_type": "UNSUPPORTED",
        "query": "Theo bạn tuần này tôi có nên đầu tư mua Bitcoin hay Ethereum không?",
        "expected_activity_slugs": [],
        "constraints": {"out_of_domain": True},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 97, "category": "Ngoài phạm vi", "intent": "UNSUPPORTED",
        "query_type": "UNSUPPORTED",
        "query": "Dự đoán giá vàng thế giới và tỷ giá USD ngày mai tăng hay giảm?",
        "expected_activity_slugs": [],
        "constraints": {"out_of_domain": True},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 98, "category": "Ngoài phạm vi", "intent": "UNSUPPORTED",
        "query_type": "UNSUPPORTED",
        "query": "Chỉ tôi cách bẻ khóa mật khẩu wifi nhà hàng xóm để xài ké mạng với.",
        "expected_activity_slugs": [],
        "constraints": {"out_of_domain": True},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 99, "category": "Ngoài phạm vi", "intent": "UNSUPPORTED",
        "query_type": "UNSUPPORTED",
        "query": "Giải giúp tôi bài toán giải tích này: tính tích phân từ 0 đến vô cùng của x*exp(-x^2).",
        "expected_activity_slugs": [],
        "constraints": {"out_of_domain": True},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
    {
        "id": 100, "category": "Ngoài phạm vi", "intent": "UNSUPPORTED",
        "query_type": "UNSUPPORTED",
        "query": "Gợi ý cho tôi danh sách các quán bar và club đêm đắt đỏ nhất Sài Gòn.",
        "expected_activity_slugs": [],
        "constraints": {"out_of_domain": True},
        "expected_card_rule": "MUST_NOT_HAVE", "min_expected_cards": 0, "max_expected_cards": 0
    },
]

# Verify all referenced slugs actually exist in corpus registry
missing_slugs = []
for q in BENCHMARK_100:
    for slug in q["expected_activity_slugs"]:
        if slug not in reg_by_slug:
            missing_slugs.append((q["id"], slug))

if missing_slugs:
    print(f"❌ CẢNH BÁO: Có {len(missing_slugs)} slug tham chiếu không tồn tại trong registry:")
    for qid, slug in missing_slugs:
        print(f"   Query #{qid}: {slug}")
else:
    print("✅ 100% slug tham chiếu trong Benchmark đều khớp chính xác với corpus_120_registry.json!")

# Save to output json
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(BENCHMARK_100, f, ensure_ascii=False, indent=2)

print(f"🎉 ĐÃ XUẤT FILE BENCHMARK 100 CÂU HỎI KÈM GROUND TRUTH:")
print(f"   Đường dẫn: {out_path}")
print(f"   Tổng số câu: {len(BENCHMARK_100)}")
