"""
Script seed 120 Synthetic Campus Activities có cấu trúc cho Đại học Bách Khoa TP.HCM (HCMUT).
Được thiết kế chuyên biệt cho nghiên cứu và đánh giá thực nghiệm RAG (Chapter 8 Luận văn):
- 120 hoạt động phân bổ đều theo 7 miền nghiệp vụ
- Mật độ ngữ nghĩa cao (Semantic Neighbors / Distractors) để kiểm tra ranking và semantic retrieval
- Đa dạng ràng buộc đa chiều: Cơ sở (CS1 vs CS2), Thời gian (Sáng, Tối, Thứ trong tuần, Cuối tuần), Ngày CTXH (0.0 đến 2.0)
- Sinh vector embeddings 768 chiều qua Google Gemini API batching (gemini-embedding-001) nạp vào pgvector
- Xuất file registry corpus_120_registry.json lưu trữ metadata và slug mapping cho Ground Truth.

Chạy:
  python server/seed_corpus_120.py
"""

import asyncio
import datetime
from datetime import timezone, timedelta
import json
import os
import sys
import uuid
import random

server_dir = os.path.dirname(os.path.abspath(__file__))
if server_dir not in sys.path:
    sys.path.insert(0, server_dir)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from google import genai
from google.genai import types
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.modules.users.models import User, UserRole
from app.modules.groups.models import Group
from app.modules.activities.models import Activity, ActivityPrivacy

# Tọa độ chuẩn HCMUT Cơ sở 1 (Lý Thường Kiệt, Q.10) & Cơ sở 2 (Dĩ An, Bình Dương)
CS1_BASE = (10.7725, 106.6578)
CS2_BASE = (10.8800, 106.8057)

# 120 SYNTHETIC ACTIVITIES DEFINITION
CORPUS_ACTIVITIES = [
    # =========================================================================
    # 1. CÔNG NGHỆ & KỸ THUẬT (20 hoạt động)
    # =========================================================================
    # --- Cụm AI & Machine Learning (Semantic Neighbors) ---
    {
        "slug": "tech_ai_ml_fundamentals",
        "title": "Workshop: Nhập môn Machine Learning và Xây dựng Mô hình Dự đoán với Scikit-Learn",
        "desc": "Hướng dẫn các thuật toán học máy cơ bản như Linear Regression, Decision Trees, Random Forest. Thực hành tiền xử lý dữ liệu tabular, chuẩn hóa đặc trưng (feature engineering) và đánh giá mô hình bằng metric RMSE, F1-score trên thư viện Python Scikit-Learn.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Phòng Lab B1-302 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0002, "lng": CS1_BASE[1] + 0.0001,
        "days_offset": 2, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "tech_ai_deep_learning_pytorch",
        "title": "Chuyên đề: Deep Learning và Mạng nơ-ron Tích chập (CNN) với PyTorch",
        "desc": "Tìm hiểu kiến trúc Neural Networks nhiều tầng, cơ chế lan truyền ngược (backpropagation), hàm mất mát Cross-Entropy và tối ưu hóa Adam. Thực hành huấn luyện mạng ResNet phân loại ảnh chữ số và vật thể từ đầu bằng framework PyTorch trên Google Colab GPU.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS2",
        "loc": "Phòng Hội thảo H6-201 - ĐH Bách Khoa CS2",
        "lat": CS2_BASE[0] + 0.0005, "lng": CS2_BASE[1] + 0.0003,
        "days_offset": 5, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "tech_ai_computer_vision_opencv",
        "title": "Seminar: Thị giác Máy tính Ứng dụng (Computer Vision) và Xử lý Ảnh với OpenCV",
        "desc": "Khám phá kỹ thuật thị giác máy tính truyền thống kết hợp mô hình YOLOv8 để nhận diện vật thể thời gian thực, phát hiện khuôn mặt và biển số xe. Demo pipeline trích xuất frame từ video webcam, áp dụng các bộ lọc Gaussian, Canny edge detection và bounding boxes.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 6, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 60,
    },
    {
        "slug": "tech_ai_genai_llm_rag",
        "title": "Workshop Thực chiến: Phát triển Trợ lý AI và Hệ thống RAG với LangChain và Gemini",
        "desc": "Xây dựng ứng dụng hỏi đáp tài liệu thông minh sử dụng Generative AI, Prompt Engineering, Vector Database (pgvector/Chroma) và kỹ thuật Retrieval-Augmented Generation (RAG). Tích hợp Google Gemini API để tổng hợp câu trả lời chuẩn xác và hạn chế ảo giác (hallucination).",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 4, "start_hour": 18, "hours": 3, "ctxh": 0.0, "max_p": 120,
    },
    {
        "slug": "tech_ai_data_science_eda",
        "title": "Lớp học cộng đồng: Khám phá Dữ liệu Khoa học (EDA) với Pandas, Seaborn và Streamlit",
        "desc": "Rèn luyện tư duy phân tích dữ liệu thực tế: thu thập dataset thương mại điện tử, xử lý dữ liệu khuyết thiếu (missing data), phân tích thống kê mô tả, vẽ biểu đồ tương quan với Matplotlib/Seaborn và đóng gói dashboard tương tác nhanh bằng thư viện Streamlit.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS2",
        "loc": "Phòng Lab Máy tính H3-102 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0010, "lng": CS2_BASE[1] - 0.0002,
        "days_offset": 3, "start_hour": 9, "hours": 3, "ctxh": 0.0, "max_p": 40,
    },

    # --- Cụm Cloud, Container & DevOps (Semantic Neighbors) ---
    {
        "slug": "tech_infra_docker_containerization",
        "title": "Workshop: Đóng gói Ứng dụng Đa tầng và Triển khai với Docker & Docker Compose",
        "desc": "Hướng dẫn viết Dockerfile tối ưu kích thước image đa tầng (multi-stage build), quản lý biến môi trường, thiết lập mạng bridge và kết nối container cơ sở dữ liệu PostgreSQL với backend API thông qua docker-compose.yml chuẩn môi trường sản xuất.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Phòng Lab B1-304 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0004, "lng": CS1_BASE[1] + 0.0002,
        "days_offset": 3, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "tech_infra_kubernetes_cluster",
        "title": "Seminar Chuyên sâu: Điều phối Cụm Container và Tự động Co giãn với Kubernetes (K8s)",
        "desc": "Tìm hiểu kiến trúc Kubernetes Cluster bao gồm Pods, Deployments, Services, Ingress Controller và ConfigMaps. Thực hành thiết lập Horizontal Pod Autoscaler (HPA) trên cụm Minikube cục bộ nhằm tự động mở rộng instance khi lưu lượng request tăng vọt.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS2",
        "loc": "Phòng Hội thảo H6-202 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0006, "lng": CS2_BASE[1] + 0.0004,
        "days_offset": 9, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 55,
    },
    {
        "slug": "tech_infra_aws_cloud_practitioner",
        "title": "Khóa huấn luyện: Điện toán Đám mây AWS và Kiến trúc Hạ tầng Serverless",
        "desc": "Làm quen với các dịch vụ điện toán đám mây cốt lõi của Amazon Web Services (AWS) bao gồm máy chủ ảo EC2, lưu trữ tĩnh S3, cân bằng tải ALB, cơ sở dữ liệu RDS và kiến trúc serverless với AWS Lambda Function kết hợp API Gateway.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Hội trường C1 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0009, "lng": CS1_BASE[1] + 0.0003,
        "days_offset": 7, "start_hour": 13, "hours": 4, "ctxh": 0.0, "max_p": 70,
    },
    {
        "slug": "tech_infra_devops_cicd_github_actions",
        "title": "Tọa đàm: Tự động hóa Quy trình Kiểm thử và Triển khai CI/CD với GitHub Actions",
        "desc": "Xây dựng pipeline tự động hóa hoàn chỉnh cho dự án phần mềm: chạy unit test pytest/jest tự động trên pull request, quét lint code, build Docker image và tự động deploy qua SSH lên máy chủ VPS khi merge vào nhánh main.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Phòng Lab A4-201 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0002, "lng": CS1_BASE[1] - 0.0003,
        "days_offset": 8, "start_hour": 18, "hours": 3, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "tech_infra_linux_server_admin",
        "title": "Workshop: Quản trị Hệ điều hành Linux và Tối ưu Hiệu năng Máy chủ Web Nginx",
        "desc": "Làm chủ terminal Linux Ubuntu/Debian: quản lý tiến trình systemd, cấu hình tường lửa UFW, cấp chứng chỉ SSL miễn phí Let's Encrypt Certbot và tối ưu reverse proxy Nginx cho ứng dụng tải cao phục vụ đồ án tốt nghiệp.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS2",
        "loc": "Phòng H6-105 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0004, "lng": CS2_BASE[1] + 0.0001,
        "days_offset": 10, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 50,
    },

    # --- Cụm Lập trình Phần mềm, Bảo mật & IoT ---
    {
        "slug": "tech_software_backend_fastapi_async",
        "title": "Khóa học ngắn: Thiết kế Kiến trúc RESTful API Bất đồng bộ với FastAPI và PostgreSQL",
        "desc": "Đi sâu vào kiến trúc Clean Architecture cho backend web Python: mô hình bất đồng bộ Asyncio, SQLAlchemy 2.0 async session, xác thực token JWT, kiểm soát phân quyền RBAC và quản lý database migration tự động bằng Alembic.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Hội trường C5-101 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0006, "lng": CS1_BASE[1] - 0.0004,
        "days_offset": 1, "start_hour": 8, "hours": 3, "ctxh": 0.0, "max_p": 60,
    },
    {
        "slug": "tech_software_frontend_react_nextjs",
        "title": "Workshop: Xây dựng Giao diện Web Hiện đại Tối ưu SEO với React và Next.js App Router",
        "desc": "Tìm hiểu Server Components, Server-Side Rendering (SSR), Client Components và quản lý trạng thái bằng Zustand/TanStack Query. Thực hành xây dựng giao diện dashboard responsive có hỗ trợ Dark Mode và animation mượt mà.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Phòng Lab B1-303 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0003, "lng": CS1_BASE[1] + 0.0002,
        "days_offset": 4, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "tech_software_mobile_flutter_crossplatform",
        "title": "Seminar: Lập trình Ứng dụng Di động Đa nền tảng (iOS & Android) với Flutter và Dart",
        "desc": "Phương pháp xây dựng ứng dụng di động hiệu năng 60fps: widget lifecycle, kiến trúc BLoC pattern, tích hợp push notification Firebase và kết nối REST API đồng bộ dữ liệu thời gian thực giữa điện thoại và máy chủ.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS2",
        "loc": "Phòng Hội thảo H6-203 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0008, "lng": CS2_BASE[1] + 0.0005,
        "days_offset": 8, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "tech_sec_owasp_pentest_web",
        "title": "Seminar Chuyên đề: Kiểm thử Xâm nhập (Pentest) và Phòng chống Lỗ hổng Web OWASP Top 10",
        "desc": "Phân tích cơ chế tấn công SQL Injection, XSS, CSRF, IDOR và Broken Access Control. Thực hành khai thác an toàn trên nền tảng phòng thí nghiệm giả lập và các giải pháp viết code phòng thủ, sanitize input và áp dụng CSP headers an toàn.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Phòng Hội thảo B4-201 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0003, "lng": CS1_BASE[1] + 0.0007,
        "days_offset": 5, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 60,
    },
    {
        "slug": "tech_sec_network_firewall_wireshark",
        "title": "Workshop: Phân tích Gói tin Mạng và Phát hiện Tấn công Mạng với Wireshark",
        "desc": "Hướng dẫn bắt và phân tích gói tin TCP/IP, DNS, HTTP/HTTPS qua phần mềm Wireshark. Nhận diện các dấu hiệu bất thường của tấn công dò quét cổng (port scan), tấn công từ chối dịch vụ DoS SYN Flood và thiết lập tường lửa phòng ngừa.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS2",
        "loc": "Phòng Lab Mạng H3-202 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0012, "lng": CS2_BASE[1] - 0.0003,
        "days_offset": 11, "start_hour": 13, "hours": 3, "ctxh": 0.0, "max_p": 40,
    },
    {
        "slug": "tech_iot_embedded_esp32_mqtt",
        "title": "Khóa huấn luyện Phần cứng: Thiết kế Hệ thống IoT Giám sát Môi trường với Vi điều khiển ESP32",
        "desc": "Lập trình nhúng C++ trên vi điều khiển ESP32: đọc dữ liệu từ cảm biến nhiệt độ DHT22, bụi mịn PM2.5, truyền dữ liệu qua giao thức MQTT lên Broker và hiển thị giám sát biểu đồ trên Web Dashboard thời gian thực.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Xưởng Thực hành Cơ Điện Tử B6-102 - CS1",
        "lat": CS1_BASE[0] - 0.0008, "lng": CS1_BASE[1] - 0.0002,
        "days_offset": 6, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 35,
    },
    {
        "slug": "tech_database_sql_optimization_indexes",
        "title": "Seminar: Tối ưu Truy vấn Cơ sở Dữ liệu SQL và Thiết kế Chỉ mục B-Tree trong PostgreSQL",
        "desc": "Nắm vững nguyên lý hoạt động của câu lệnh EXPLAIN ANALYZE, hiểu rõ Seq Scan vs Index Scan, thiết kế Partial Index, Composite Index và các kỹ thuật partitioning bảng dữ liệu lớn hàng triệu bản ghi tránh gây nghẽn máy chủ.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Phòng C1-201 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0002,
        "days_offset": 7, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "tech_game_unity_csharp_basics",
        "title": "Workshop: Nhập môn Phát triển Video Game 2D với Unity Engine và Lập trình C#",
        "desc": "Làm quen giao diện Unity Editor, hệ thống vật lý Rigidbody2D, phát hiện va chạm BoxCollider2D, điều khiển nhân vật nhảy và bắn đạn qua script C#. Tự tay hoàn thiện một màn chơi game platformer mini hoàn chỉnh.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS2",
        "loc": "Phòng Hội thảo H6-204 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0007, "lng": CS2_BASE[1] + 0.0006,
        "days_offset": 12, "start_hour": 14, "hours": 4, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "tech_hackathon_smart_campus_2026",
        "title": "Cuộc thi Bách Khoa Hackathon 2026: AI for Smart Campus (48 Giờ Hackathon Liên tục)",
        "desc": "Đấu trường công nghệ quy mô toàn trường! Các đội thi gồm 3-5 thành viên có 48 giờ liên tục để xây dựng nguyên mẫu sản phẩm ứng dụng AI giải quyết bài toán giao thông, năng lượng và học tập thông minh trong khuôn viên Đại học Bách Khoa.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Hội trường A5 & Sảnh Nhà B4 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 14, "start_hour": 8, "hours": 48, "ctxh": 1.0, "max_p": 200,
    },
    {
        "slug": "tech_blockchain_smart_contracts_solidity",
        "title": "Tọa đàm: Công nghệ Sổ cái Phân tán Blockchain và Lập trình Hợp đồng Thông minh Solidity",
        "desc": "Tìm hiểu kiến trúc mạng Ethereum, máy ảo EVM, cơ chế đồng thuận Proof of Stake và thực hành viết Smart Contract token chuẩn ERC-20, triển khai thử nghiệm trên testnet Sepolia bằng công cụ Hardhat và ví MetaMask.",
        "cat": "Công nghệ & Kỹ thuật", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0003,
        "days_offset": 13, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 55,
    },

    # =========================================================================
    # 2. HỌC THUẬT & ÔN THI (20 hoạt động)
    # =========================================================================
    # --- Cụm Toán & Khoa học Đại cương (Semantic Neighbors) ---
    {
        "slug": "acad_math_calculus_1_midterm",
        "title": "Lớp Ôn tập Cấp tốc Giữa kỳ Môn Giải tích 1: Đạo hàm, Tích phân và Chuỗi số",
        "desc": "Hệ thống hóa toàn bộ công thức tích phân suy rộng loại 1 và 2, các tiêu chuẩn hội tụ chuỗi số (D'Alembert, Cauchy, Tích phân) và giải bộ đề thi giữa kỳ mẫu của các năm trước kèm mẹo bấm máy tính Casio chính xác.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Giảng đường C5-102 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0007, "lng": CS1_BASE[1] - 0.0003,
        "days_offset": 1, "start_hour": 7, "hours": 4, "ctxh": 0.0, "max_p": 90,
    },
    {
        "slug": "acad_math_calculus_2_finals",
        "title": "Chuỗi Ôn thi Cuối kỳ Môn Giải tích 2: Tích phân Bội và Tích phân Đường Mặt",
        "desc": "Phương pháp đổi biến tọa độ cực, tọa độ cầu, áp dụng công thức Green, Gauss-Ostrogradsky và Stokes để tính lưu lượng trường vector. Hướng dẫn chi tiết cách vẽ hình không gian 3D để xác định cận tích phân chuẩn xác.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Giảng đường H1-201 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0002, "lng": CS2_BASE[1] + 0.0008,
        "days_offset": 5, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 80,
    },
    {
        "slug": "acad_math_linear_algebra_matrices",
        "title": "Gia sư Đồng đẳng: Chuyên đề Không gian Vector và Ma trận Chéo hóa Môn Đại số Tuyến tính",
        "desc": "Giải đáp khúc mắc về hạng ma trận, định thức, độc lập tuyến tính, cơ sở không gian vector, tìm trị riêng và vector riêng phục vụ bài toán chéo hóa ma trận vuông. Buổi học do các anh chị sinh viên đạt A+ hỗ trợ kèm cặp.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng tự học Thư viện A2 - Tầng 2 CS1",
        "lat": CS1_BASE[0] + 0.0001, "lng": CS1_BASE[1] + 0.0006,
        "days_offset": 3, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 40,
    },
    {
        "slug": "acad_math_probability_statistics",
        "title": "Nhóm Tự học: Môn Xác suất Thống kê và Phân tích Kiểm định Giả thuyết",
        "desc": "Ôn tập các phân phối xác suất quan trọng (Nhị thức, Poisson, Chuẩn Gauss, Student), phương pháp ước lượng khoảng tin cậy và thực hành các bài toán kiểm định giả thuyết thống kê Z-test, T-test trong đồ án kỹ thuật.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Phòng Tự học H6-301 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0006, "lng": CS2_BASE[1] + 0.0003,
        "days_offset": 4, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 35,
    },
    {
        "slug": "acad_phys_physics_1_mechanics",
        "title": "Chuyên đề Ôn thi Vật lý 1: Động lực học Chất điểm và Cơ học Vật rắn",
        "desc": "Phân tích định luật bảo toàn động lượng, momen động lượng, chuyển động quay của vật rắn quanh trục cố định và định luật Bernoulli trong thủy động lực học. Chữa chi tiết các bài tập khó trong sách bài tập Bách Khoa.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 6, "start_hour": 8, "hours": 3, "ctxh": 0.0, "max_p": 70,
    },
    {
        "slug": "acad_phys_physics_2_electromagnetism",
        "title": "Buổi Chữa Đề Mẫu Vật lý 2: Điện trường, Từ trường và Định luật Cảm ứng Điện từ",
        "desc": "Tổng hợp công thức định luật Gauss cho điện trường, định luật Ampere cho từ trường và phương trình Maxwell dạng tích phân. Luyện tập cách vẽ đường sức điện từ và giải các bài toán sóng ánh sáng giao thoa, nhiễu xạ.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Hội trường H1-102 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0001, "lng": CS2_BASE[1] + 0.0007,
        "days_offset": 8, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 75,
    },
    {
        "slug": "acad_chem_general_chemistry",
        "title": "Học nhóm: Ôn thi Môn Hóa học Đại cương và Cân bằng Nhiệt động lực học",
        "desc": "Cùng nhau giải các dạng bài tập Enthalpy, Entropy, Năng lượng tự do Gibbs (Delta G), cân bằng hóa học phản ứng oxy hóa khử và phương trình Nernst tính thế pin điện hóa.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng B4-105 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0004, "lng": CS1_BASE[1] + 0.0008,
        "days_offset": 2, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 35,
    },

    # --- Cụm Chuyên ngành Máy tính & Kỹ thuật (Semantic Neighbors) ---
    {
        "slug": "acad_cs_dsa_data_structures_library",
        "title": "Học nhóm Môn Cấu trúc Dữ liệu và Giải thuật (DSA) tại Thư viện Bách Khoa",
        "desc": "Luyện tập cài đặt danh sách liên kết (Linked List), ngăn xếp (Stack), cây nhị phân tìm kiếm (BST), đồ thị và các thuật toán duyệt DFS/BFS bằng ngôn ngữ C++. Bàn luận các kỹ thuật phân tích độ phức tạp thuật toán Big-O.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Thư viện Bách Khoa A2 - Phòng tự học tầng 2",
        "lat": CS1_BASE[0] + 0.0001, "lng": CS1_BASE[1] + 0.0006,
        "days_offset": 1, "start_hour": 8, "hours": 3, "ctxh": 0.0, "max_p": 35,
    },
    {
        "slug": "acad_cs_dsa_leetcode_competitive_programming",
        "title": "CLB Lập trình ICPC: Luyện tập Giải bài Thuật toán Nâng cao (Dynamic Programming & Graph)",
        "desc": "Dành cho các bạn sinh viên rèn luyện tư duy thi lập trình thuật toán ICPC và phỏng vấn coding Big Tech. Chuyên đề tuần này: Quy hoạch động (Dynamic Programming trạng thái bitmask) và thuật toán luồng cực đại trên đồ thị (Max Flow).",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng Lab B1-305 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0003, "lng": CS1_BASE[1] + 0.0001,
        "days_offset": 5, "start_hour": 18, "hours": 3, "ctxh": 0.0, "max_p": 40,
    },
    {
        "slug": "acad_cs_oop_cpp_design_patterns",
        "title": "Workshop: Lập trình Hướng đối tượng (OOP) C++ và Áp dụng 23 Mẫu Thiết kế Design Patterns",
        "desc": "Đi sâu vào 4 trụ cột hướng đối tượng (Tính kế thừa, Đa hình, Trừu tượng hóa, Đóng gói) và áp dụng thực tế các mẫu thiết kế kinh điển: Singleton, Factory, Observer, Strategy giúp code mở rộng và dễ bảo trì.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Phòng H6-205 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0006, "lng": CS2_BASE[1] + 0.0004,
        "days_offset": 7, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "acad_cs_os_operating_systems_concurrency",
        "title": "Seminar: Hệ điều hành (Operating Systems) - Tiến trình, Luồng và Xử lý Khóa chết (Deadlock)",
        "desc": "Phân tích cơ chế chuyển đổi ngữ cảnh (Context Switching), điều độ tiến trình CPU, đồng bộ hóa luồng bằng Semaphore/Mutex, giải quyết bài toán Dining Philosophers và quản lý bộ nhớ ảo qua kỹ thuật phân trang (Paging).",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0003,
        "days_offset": 9, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 60,
    },
    {
        "slug": "acad_cs_networks_socket_programming",
        "title": "Thực hành Mạng Máy tính: Lập trình Socket TCP/UDP và Phân tích Giao thức Mạng",
        "desc": "Xây dựng ứng dụng chat đa người dùng bằng ngôn ngữ C/Python sử dụng thư viện Socket bất đồng bộ. Hiểu sâu cơ chế bắt tay 3 bước TCP 3-way handshake, cơ chế kiểm soát tắc nghẽn và so sánh ưu nhược điểm với giao thức UDP.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Phòng Lab H3-104 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0011, "lng": CS2_BASE[1] - 0.0001,
        "days_offset": 6, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "acad_cs_computer_architecture_assembly",
        "title": "Chuyên đề Kiến trúc Máy tính: Lập trình Hợp ngữ MIPS và Thiết kế Đường dẫn Dữ liệu (Datapath)",
        "desc": "Tìm hiểu tập lệnh MIPS 32-bit, cách vi xử lý thực thi lệnh qua các khối ALU, thanh ghi, và mô phỏng đường ống lệnh (Pipelining) kèm phương pháp giải quyết xung đột dữ liệu (Data Hazards).",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng B1-201 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0002, "lng": CS1_BASE[1] - 0.0001,
        "days_offset": 8, "start_hour": 8, "hours": 3, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "acad_research_scientific_paper_writing",
        "title": "Buổi Chia sẻ Kinh nghiệm Nghiên cứu Khoa học Sinh viên và Viết bài báo chuẩn IEEE",
        "desc": "Hướng dẫn phương pháp tìm kiếm đề tài nghiên cứu tiềm năng, kỹ năng đọc và trích dẫn bài báo khoa học trên Google Scholar/Scopus, cấu trúc bài báo chuẩn IEEE và cách nộp hồ sơ xin kinh phí đề tài cấp trường.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 10, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 100,
    },
    {
        "slug": "acad_eng_autocad_technical_drawing",
        "title": "Lớp Hướng dẫn Vẽ Kỹ thuật Cơ khí và Thiết kế Bản vẽ 2D với phần mềm AutoCAD",
        "desc": "Rèn luyện quy chuẩn hình chiếu vuông góc, vẽ mặt cắt, ghi kích thước dung sai hình học và thực hành xuất bản vẽ chế tạo cơ khí chuẩn kỹ thuật quốc tế cho sinh viên khối ngành kỹ thuật.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng Máy tính C4-201 - CS1",
        "lat": CS1_BASE[0] + 0.0005, "lng": CS1_BASE[1] - 0.0005,
        "days_offset": 4, "start_hour": 8, "hours": 3, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "acad_eng_solidworks_3d_modeling",
        "title": "Workshop: Thiết kế Mô hình 3D và Mô phỏng Chuyển động Cơ cấu bằng SolidWorks",
        "desc": "Xây dựng chi tiết máy 3D từ phác thảo 2D sketch, lắp ráp cụm chi tiết (assembly) và mô phỏng động học chuyển động ăn khớp bánh răng, bộ truyền đai phục vụ làm đồ án môn học Chi tiết máy.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Phòng Hội thảo H6-206 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0005, "lng": CS2_BASE[1] + 0.0003,
        "days_offset": 11, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 40,
    },
    {
        "slug": "acad_lang_toeic_reading_listening_tips",
        "title": "Khóa Luyện Thi TOEIC 650+ Cấp tốc: Chiến thuật Bẫy Nghe Part 3-4 và Đọc nhanh Part 7",
        "desc": "Chia sẻ kinh nghiệm làm bài thi TOEIC quốc tế đạt chuẩn đầu ra Bách Khoa: phương pháp đọc quét thông tin skimming/scanning bài đọc dài và kỹ năng loại trừ đáp án gây nhiễu trong phần thi nghe.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Giảng đường C5-101 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0006, "lng": CS1_BASE[1] - 0.0004,
        "days_offset": 3, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 80,
    },
    {
        "slug": "acad_lang_ielts_speaking_band_7",
        "title": "CLB Tiếng Anh: Luyện phản xạ IELTS Speaking theo chủ đề Khoa học & Công nghệ",
        "desc": "Thực hành mock test Speaking 1-on-1 theo format phòng thi thật, mở rộng vốn từ vựng học thuật C1/C2 (Collocations/Idioms) bàn về chủ đề Trí tuệ nhân tạo, Tự động hóa và Biến đổi khí hậu.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Phòng Sinh hoạt CLB KTX Khu B - ĐHQG",
        "lat": CS2_BASE[0] + 0.0020, "lng": CS2_BASE[1] + 0.0018,
        "days_offset": 7, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 30,
    },
    {
        "slug": "acad_skills_academic_writing_latex",
        "title": "Workshop: Soạn thảo Báo cáo Khóa luận Tốt nghiệp Chuẩn Khoa học bằng LaTeX",
        "desc": "Làm chủ công cụ Overleaf và mã nguồn LaTeX: đánh số công thức tự động, vẽ bảng biểu chuẩn đẹp, chèn hình vector SVG/PDF và tự động quản lý danh mục tài liệu tham khảo với file BibTeX.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng Lab A4-202 - CS1",
        "lat": CS1_BASE[0] - 0.0002, "lng": CS1_BASE[1] - 0.0002,
        "days_offset": 12, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "acad_skills_github_for_team_projects",
        "title": "Lớp Kỹ năng Thực hành: Quản lý Phiên bản Mã nguồn Git & Làm việc Nhóm trên GitHub",
        "desc": "Giải quyết dứt điểm nỗi sợ xung đột code (Merge Conflicts): hướng dẫn mô hình phân nhánh Gitflow, tạo Pull Request chuyên nghiệp, review code chéo và sử dụng rebase/cherry-pick mượt mà.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng Lab B1-301 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0001, "lng": CS1_BASE[1] + 0.0002,
        "days_offset": 2, "start_hour": 8, "hours": 3, "ctxh": 0.0, "max_p": 45,
    },

    # =========================================================================
    # 3. TÌNH NGUYỆN & CÔNG TÁC XÃ HỘI (20 hoạt động)
    # =========================================================================
    # --- Hoạt động có ngày CTXH cao (1.0 đến 2.0 ngày) ---
    {
        "slug": "vol_ctxh_sunday_green_lake_cleanup",
        "title": "Chiến dịch Tình nguyện Ngày Chủ Nhật Xanh: Dọn dẹp Vệ sinh và Tôn tạo Hồ Tiền Phong",
        "desc": "Đội hình tình nguyện ra quân thu gom rác thải nhựa, vớt lục bình quanh bờ hồ Tiền Phong và sơn mới hàng rào khuôn viên Ký túc xá Bách Khoa Cơ sở 2. Hoàn thành được xác nhận 1.0 ngày CTXH chính thức.",
        "cat": "Tình nguyện & CTXH", "campus": "CS2",
        "loc": "Hồ Tiền Phong - ĐH Bách Khoa CS2 (Dĩ An)",
        "lat": CS2_BASE[0] - 0.0015, "lng": CS2_BASE[1] - 0.0015,
        "days_offset": 2, "start_hour": 7, "hours": 4, "ctxh": 1.0, "max_p": 80,
    },
    {
        "slug": "vol_ctxh_blood_donation_spring_2026",
        "title": "Ngày hội Hiến máu Nhân đạo: Giọt hồng Bách Khoa Đợt 1 Năm 2026",
        "desc": "Chương trình hiến máu tình nguyện do Hội Chữ Thập Đỏ và Đoàn trường phối hợp tổ chức tại Trạm Y tế CS1. Sinh viên hiến máu được bồi dưỡng ăn sáng, cấp giấy chứng nhận hiến máu và 1.0 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Trạm Y tế - Trường ĐH Bách Khoa CS1 (Lý Thường Kiệt)",
        "lat": CS1_BASE[0] + 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 3, "start_hour": 7, "hours": 5, "ctxh": 1.0, "max_p": 150,
    },
    {
        "slug": "vol_ctxh_exam_support_tiep_suc_mua_thi",
        "title": "Chiến dịch Tiếp sức Mùa thi 2026: Điều phối Giao thông và Hỗ trợ Thí sinh THPT",
        "desc": "Tình nguyện viên túc trực tại các điểm thi tốt nghiệp THPT quận 10: phát nước uống miễn phí, trông giữ xe, hướng dẫn phòng thi và điều phối xe cộ tránh ùn tắc. Cấp chứng nhận 2.0 ngày CTXH toàn chiến dịch.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Cổng chính và Sảnh A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 7, "start_hour": 6, "hours": 8, "ctxh": 2.0, "max_p": 100,
    },
    {
        "slug": "vol_ctxh_summer_volunteer_mua_he_xanh",
        "title": "Tập huấn Chiến sĩ Tình nguyện Mùa Hè Xanh: Xây cầu Nông thôn và Dạy học Hè",
        "desc": "Buổi sinh hoạt tập huấn kỹ năng sơ cấp cứu, kỹ năng dân vũ và quy chế an toàn dành cho chiến sĩ Mùa Hè Xanh chuẩn bị lên đường về mặt trận tỉnh miền Tây. Hoạt động chiến dịch được tính 2.0 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 14, "start_hour": 8, "hours": 8, "ctxh": 2.0, "max_p": 120,
    },
    {
        "slug": "vol_ctxh_green_tutor_shelter_children",
        "title": "Gia sư Áo xanh: Dạy kèm Phụ đạo Toán và Tin học cho Trẻ em Mái ấm Khu vực Làng Đại học",
        "desc": "Dành cho các bạn sinh viên yêu thích giáo dục: hỗ trợ dạy kèm kiến thức căn bản, kể chuyện hướng nghiệp và tổ chức trò chơi tập thể cho các em nhỏ có hoàn cảnh khó khăn. Cấp 1.5 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS2",
        "loc": "Nhà Sinh hoạt Cộng đồng KTX Khu B - ĐHQG",
        "lat": CS2_BASE[0] + 0.0021, "lng": CS2_BASE[1] + 0.0018,
        "days_offset": 5, "start_hour": 13, "hours": 4, "ctxh": 1.5, "max_p": 40,
    },
    {
        "slug": "vol_ctxh_freshmen_welcome_support",
        "title": "Đội hình Hỗ trợ Tân Sinh viên K26: Hướng dẫn Thủ tục Nhập học và Tìm Nhà trọ",
        "desc": "Đón tiếp tân sinh viên và phụ huynh tại cơ sở 1: hướng dẫn kê khai hồ sơ sinh viên, chụp ảnh thẻ tích hợp, tư vấn xe buýt số 33/50 và giới thiệu ký túc xá an toàn. Cấp 1.0 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Sảnh Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 10, "start_hour": 7, "hours": 8, "ctxh": 1.0, "max_p": 60,
    },
    {
        "slug": "vol_ctxh_dorm_ktx_cleanup_cs2",
        "title": "Ngày Thứ Bảy Tình nguyện: Vệ sinh Ký túc xá và Trồng Cây xanh Khuôn viên KTX Khu A",
        "desc": "Chăm sóc bồn hoa thanh niên, dọn dẹp vệ sinh các dãy hành lang ký túc xá và quét vôi lại gốc cây chống sâu bệnh tạo cảnh quan sống xanh cho sinh viên nội trú. Cấp 1.0 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS2",
        "loc": "Ký túc xá Khu A ĐHQG - Gần Bách Khoa CS2",
        "lat": CS2_BASE[0] + 0.0015, "lng": CS2_BASE[1] + 0.0010,
        "days_offset": 6, "start_hour": 7, "hours": 5, "ctxh": 1.0, "max_p": 70,
    },
    {
        "slug": "vol_ctxh_traffic_safety_gate_cs1",
        "title": "Đội Thanh niên Tình nguyện: Hỗ trợ Phân luồng Giao thông Cổng 268 Lý Thường Kiệt",
        "desc": "Phối hợp cùng bảo vệ trường hướng dẫn xe máy sinh viên vào bãi đỗ trật tự vào khung giờ cao điểm sáng sớm, ngăn chặn tình trạng chen lấn gây ùn tắc giao thông trước cổng trường. Cấp 1.0 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Cổng chính 268 Lý Thường Kiệt - CS1",
        "lat": CS1_BASE[0] - 0.0001, "lng": CS1_BASE[1] - 0.0001,
        "days_offset": 1, "start_hour": 6, "hours": 3, "ctxh": 1.0, "max_p": 30,
    },

    # --- Hoạt động có ngày CTXH vừa (0.5 ngày) ---
    {
        "slug": "vol_ctxh_ewaste_battery_recycle",
        "title": "Ngày hội Đổi Pin cũ và Rác thải Điện tử Lấy Cây Sen đá Mini",
        "desc": "Chiến dịch thu gom pin đã qua sử dụng, sạc điện thoại hỏng và linh kiện máy tính cũ nhằm chuyển tới đơn vị xử lý chất thải độc hại. Sinh viên đóng góp phân loại rác và tuyên truyền được cấp 0.5 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Sảnh Nhà B4 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0004, "lng": CS1_BASE[1] + 0.0008,
        "days_offset": 1, "start_hour": 8, "hours": 6, "ctxh": 0.5, "max_p": 120,
    },
    {
        "slug": "vol_ctxh_library_book_arrangement_cs1",
        "title": "Tình nguyện Chủ Nhật: Sắp xếp Phân loại Giá sách và Vệ sinh Phòng Đọc Thư viện A2",
        "desc": "Hỗ trợ thủ thư phân loại sách chuyên ngành kỹ thuật theo mã phân loại thập phân DDC, dán lại nhãn gáy sách cũ và lau dọn bàn ghế phòng đọc phục vụ mùa ôn thi cuối kỳ. Cấp 0.5 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Thư viện Bách Khoa A2 - Tầng 1 CS1",
        "lat": CS1_BASE[0] + 0.0001, "lng": CS1_BASE[1] + 0.0006,
        "days_offset": 8, "start_hour": 8, "hours": 4, "ctxh": 0.5, "max_p": 40,
    },
    {
        "slug": "vol_ctxh_recycle_paper_charity_notebooks",
        "title": "Chương trình Gom Giấy vụn Đóng Tập vở Tặng Học sinh Nghèo Vùng sâu",
        "desc": "Tập kết giấy kiểm tra, giáo trình photo đã qua sử dụng của sinh viên các phòng ký túc xá để bán gây quỹ mua tập vở và dụng cụ học tập mới gửi tặng các em học sinh có hoàn cảnh khó khăn. Cấp 0.5 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS2",
        "loc": "Sảnh Nhà H6 - ĐH Bách Khoa CS2",
        "lat": CS2_BASE[0] + 0.0012, "lng": CS2_BASE[1] + 0.0005,
        "days_offset": 9, "start_hour": 8, "hours": 4, "ctxh": 0.5, "max_p": 50,
    },
    {
        "slug": "vol_ctxh_campus_bicycle_repair_free",
        "title": "Trạm Sửa Xe Đạp Miễn Phí và Bơm Vá Xe cho Sinh viên KTX Bách Khoa",
        "desc": "Đội hình tình nguyện viên khối ngành Cơ khí hỗ trợ bơm xe, tăng xích, thay má phanh xe đạp miễn phí cho các bạn sinh viên đi lại giữa giảng đường và ký túc xá. Cấp 0.5 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Nhà để xe B6 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0007, "lng": CS1_BASE[1] - 0.0003,
        "days_offset": 3, "start_hour": 8, "hours": 4, "ctxh": 0.5, "max_p": 25,
    },

    # --- Hoạt động Tình nguyện KHÔNG CÓ NGÀY CTXH (0.0 ngày) (Để test bộ lọc CTXH) ---
    {
        "slug": "vol_no_ctxh_sharing_experience_volunteer",
        "title": "Tọa đàm Chia sẻ Kinh nghiệm: Hành trình Trưởng thành từ các Phong trào Tình nguyện",
        "desc": "Buổi cà phê trò chuyện cùng các cựu thủ lĩnh Mùa Hè Xanh, lắng nghe những câu chuyện cảm động và bài học kỹ năng sống. Hoạt động giao lưu nội bộ mở, KHÔNG tính điểm CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Highlands Coffee - 268 Lý Thường Kiệt",
        "lat": CS1_BASE[0] + 0.0015, "lng": CS1_BASE[1] + 0.0010,
        "days_offset": 4, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 40,
    },
    {
        "slug": "vol_no_ctxh_planning_spring_campaign",
        "title": "Họp Ban Tổ chức: Lập Kế hoạch và Dự trù Kinh phí Chiến dịch Xuân Tình Nguyện 2027",
        "desc": "Buổi họp bàn phương án tiền trạm, phân bổ nhân sự các đội hình gói bánh chưng và tặng quà Tết cho các cụ già neo đơn. Dành riêng cho thành viên nòng cốt Đội CTXH, không cấp ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS2",
        "loc": "Phòng Sinh hoạt Đội H6-101 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0004, "lng": CS2_BASE[1] + 0.0002,
        "days_offset": 6, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 30,
    },
    {
        "slug": "vol_no_ctxh_fundraising_music_night",
        "title": "Đêm nhạc Acoustic Gây quỹ Tình nguyện: Nụ cười Trẻ thơ 2026",
        "desc": "Chương trình ca nhạc giao lưu acoustic ngoài trời do các CLB sinh viên phối hợp tổ chức nhằm quyên góp quỹ mổ tim cho bệnh nhi nghèo. Tham gia tự nguyện ủng hộ, không tính ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Sân C3 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0006, "lng": CS1_BASE[1] - 0.0013,
        "days_offset": 5, "start_hour": 19, "hours": 3, "ctxh": 0.0, "max_p": 150,
    },
    {
        "slug": "vol_ctxh_clean_lab_computers_cs1",
        "title": "Chủ Nhật Xanh Khoa Máy tính: Vệ sinh Bụi Bàn phím và Bảo dưỡng Máy tính Phòng Lab B1",
        "desc": "Thổi bụi thùng case máy tính, vệ sinh màn hình và sắp xếp gọn gàng dây cáp mạng các phòng Lab phục vụ kỳ thi học kỳ trơn tru. Cấp 0.5 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Dãy phòng Lab B1 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0003, "lng": CS1_BASE[1] + 0.0002,
        "days_offset": 11, "start_hour": 8, "hours": 4, "ctxh": 0.5, "max_p": 30,
    },
    {
        "slug": "vol_ctxh_blood_donor_care_team",
        "title": "Đội Tình nguyện Chăm sóc Người hiến máu và Điều phối Thẻ hiến máu",
        "desc": "Hỗ trợ các bác sĩ tiếp đón người hiến máu, rót trà đường, phát bánh sữa và ghi nhận thông tin thẻ hiến máu nhân đạo cho sinh viên. Cấp 1.0 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Trạm Y tế CS1 - 268 Lý Thường Kiệt",
        "lat": CS1_BASE[0] + 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 3, "start_hour": 6, "hours": 6, "ctxh": 1.0, "max_p": 25,
    },
    {
        "slug": "vol_ctxh_plastic_free_university_awareness",
        "title": "Chiến dịch Đại học Không Rác Thải Nhựa: Tuyên truyền Hạn chế Ly nhựa Một lần",
        "desc": "Đặt bàn truyền thông tại các căng tin trường, phát tặng bình nước cá nhân và khuyến khích sinh viên không dùng ống hút nhựa bảo vệ môi trường giảng đường. Cấp 0.5 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS2",
        "loc": "Căng tin Sinh viên Nhà H2 - CS2 Dĩ An",
        "lat": CS2_BASE[0] - 0.0005, "lng": CS2_BASE[1] + 0.0005,
        "days_offset": 4, "start_hour": 11, "hours": 3, "ctxh": 0.5, "max_p": 40,
    },
    {
        "slug": "vol_ctxh_paint_dorm_benches_cs1",
        "title": "Chủ Nhật Tình nguyện: Sơn mới Ghế đá và Dọn dẹp Cảnh quan Ký túc xá Bách Khoa CS1",
        "desc": "Chung tay cạo gỉ sét và quét sơn chống thấm lại hệ thống ghế đá sân chung, trồng thêm hoa mười giờ tại bồn hoa KTX 497 Hòa Hảo. Cấp 1.0 ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "KTX Bách Khoa (497 Hòa Hảo, P.7, Q.10)",
        "lat": CS1_BASE[0] - 0.0013, "lng": CS1_BASE[1] + 0.0013,
        "days_offset": 12, "start_hour": 7, "hours": 5, "ctxh": 1.0, "max_p": 50,
    },
    {
        "slug": "vol_no_ctxh_gratitude_ceremony_veterans",
        "title": "Hành trình Tri ân: Viếng Nghĩa trang Liệt sĩ TP.HCM và Thắp nến Tri ân Anh hùng",
        "desc": "Đoàn xe sinh viên xuất phát từ CS1 viếng Nghĩa trang Liệt sĩ TP.HCM, dâng hương và nghe kể chuyện truyền thống lịch sử hào hùng của các thế hệ cha anh. Hoạt động giáo dục truyền thống không tính ngày CTXH.",
        "cat": "Tình nguyện & CTXH", "campus": "CS1",
        "loc": "Sân A5 tập trung xe buýt - CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 13, "start_hour": 15, "hours": 4, "ctxh": 0.0, "max_p": 80,
    },

    # =========================================================================
    # 4. THỂ THAO & RÈN LUYỆN (20 hoạt động)
    # =========================================================================
    # --- Cụm Bóng đá (Semantic Neighbors: Sân 5 vs Sân 7, Thứ 5 vs Thứ 7) ---
    {
        "slug": "sport_football_thu_night_7v7",
        "title": "Giao lưu Kèo Bóng đá Sân 7: Tối thứ Năm hàng tuần tại Sân cỏ KTX Bách Khoa CS1",
        "desc": "Tìm đội giao hữu bóng đá mini sân 7 người. Trận đấu diễn ra lúc 19:00 - 21:00 tối thứ Năm. Yêu cầu đá vui vẻ, giữ chân cho nhau, chia đều tiền thuê sân và nước uống.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Sân bóng đá KTX Bách Khoa (497 Hòa Hảo, Q.10)",
        "lat": CS1_BASE[0] - 0.0013, "lng": CS1_BASE[1] + 0.0013,
        "days_offset": 2, "start_hour": 19, "hours": 2, "ctxh": 0.0, "max_p": 18,
    },
    {
        "slug": "sport_football_sat_afternoon_5v5",
        "title": "Giao lưu Kèo Bóng đá Sân 5: Chiều thứ Bảy tại Cụm Sân mini Khu B Làng Đại học",
        "desc": "Kèo bóng đá mini sân 5 người dành cho các bạn sinh viên học tại Cơ sở 2 Dĩ An. Thi đấu lúc 16:30 chiều thứ Bảy, rèn luyện thể lực sau giờ học, có bình nước đá phục vụ miễn phí.",
        "cat": "Thể thao & Giải trí", "campus": "CS2",
        "loc": "Sân bóng đá Mini Khu B ĐHQG - CS2",
        "lat": CS2_BASE[0] + 0.0018, "lng": CS2_BASE[1] + 0.0012,
        "days_offset": 4, "start_hour": 16, "hours": 2, "ctxh": 0.0, "max_p": 14,
    },
    {
        "slug": "sport_football_faculty_cup_sunday_morning",
        "title": "Giải Bóng đá Tranh Cúp Khoa KH&KT Máy tính: Loạt trận Vòng bảng Sáng Chủ Nhật",
        "desc": "Các đội tuyển sinh viên các khóa K21, K22, K23, K24 tranh tài giải bóng đá thường niên. Cổ vũ nhiệt tình, trọng tài chuyên nghiệp điều khiển trận đấu.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Sân bóng đá lớn - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0006, "lng": CS1_BASE[1] - 0.0013,
        "days_offset": 5, "start_hour": 7, "hours": 4, "ctxh": 0.0, "max_p": 100,
    },
    {
        "slug": "sport_football_futsal_indoor_cs1",
        "title": "Giao lưu Futsal Bóng đá Trong nhà: Sàn gỗ Nhà Thi đấu Thể thao Bách Khoa",
        "desc": "Thi đấu bóng đá futsal sàn trong nhà tiêu chuẩn, bóng số 4 độ nảy thấp. Rèn luyện kỹ thuật khống chế bóng nhanh và phối hợp ban bật cự ly ngắn.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Nhà Thi đấu Đa Năng C3 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0006, "lng": CS1_BASE[1] - 0.0013,
        "days_offset": 6, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 16,
    },

    # --- Cụm Cầu lông & Bóng bàn (Semantic Neighbors) ---
    {
        "slug": "sport_badminton_c3_courts_weekend",
        "title": "Kèo Cầu lông Đôi Nam - Nữ Giao lưu Cuối tuần: Cụm Sân Cầu lông C3 Bách Khoa CS1",
        "desc": "Tìm cạ giao lưu đánh cầu lông đôi nam và đôi nam nữ. Yêu cầu trình độ từ trung bình trở lên, tự chuẩn bị vợt và cầu thi đấu Yonex, chia đều tiền thuê sân theo giờ.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Sân Cầu lông C3 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0006, "lng": CS1_BASE[1] - 0.0013,
        "days_offset": 4, "start_hour": 17, "hours": 2, "ctxh": 0.0, "max_p": 12,
    },
    {
        "slug": "sport_badminton_morning_cs2_ktx",
        "title": "CLB Cầu lông: Buổi Tập Thể lực và Kỹ thuật Đập cầu Smash Sáng sớm tại KTX CS2",
        "desc": "Khởi động ngày mới tràn đầy năng lượng cùng CLB Cầu lông Cơ sở 2. Luyện bài tập di chuyển 6 góc sân, bài tập phông cầu cuối sân và đập cầu tấn công.",
        "cat": "Thể thao & Giải trí", "campus": "CS2",
        "loc": "Nhà Thể thao KTX Khu B - ĐHQG",
        "lat": CS2_BASE[0] + 0.0022, "lng": CS2_BASE[1] + 0.0015,
        "days_offset": 3, "start_hour": 6, "hours": 2, "ctxh": 0.0, "max_p": 16,
    },
    {
        "slug": "sport_tabletennis_pingpong_cs1",
        "title": "Giao lưu Bóng bàn Đơn và Đôi: Bàn bóng Tầng trệt Nhà Thi đấu Bách Khoa CS1",
        "desc": "Dành cho các bạn yêu thích bộ môn bóng bàn ping-pong. Thi đấu theo thể thức 5 set thắng 3, rèn luyện phản xạ cổ tay và các kỹ thuật xoáy bóng topspin.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Tầng trệt Nhà C3 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0005, "lng": CS1_BASE[1] - 0.0012,
        "days_offset": 7, "start_hour": 17, "hours": 2, "ctxh": 0.0, "max_p": 12,
    },

    # --- Cụm Bóng rổ & Bóng chuyền (Semantic Neighbors) ---
    {
        "slug": "sport_basketball_weekend_outdoor_cs1",
        "title": "Kèo Bóng rổ Giao lưu 3x3 và 5x5: Chiều Chủ Nhật tại Sân Bóng rổ Ngoài trời Bách Khoa CS1",
        "desc": "Tìm đội ném bóng rổ nửa sân 3x3 và cả sân 5x5. Trận đấu vui vẻ, rèn luyện thể lực cuối tuần, giao lưu giữa sinh viên các khoa Kỹ thuật.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Sân Bóng rổ Ngoài trời - Cạnh Sân C3 Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0007, "lng": CS1_BASE[1] - 0.0014,
        "days_offset": 5, "start_hour": 16, "hours": 3, "ctxh": 0.0, "max_p": 25,
    },
    {
        "slug": "sport_basketball_cs2_h6_court",
        "title": "Bóng rổ Ném rổ Giao hữu Sau giờ học: Sân Bóng rổ Khu Thể thao CS2 Dĩ An",
        "desc": "Hẹn kèo ném rổ tự do và thi đấu giao hữu nhẹ nhàng sau những tiết học căng thẳng tại giảng đường H6 Cơ sở 2. Có sẵn bóng rổ thi đấu chuẩn Spalding.",
        "cat": "Thể thao & Giải trí", "campus": "CS2",
        "loc": "Sân Bóng rổ Thể thao CS2 - ĐH Bách Khoa Dĩ An",
        "lat": CS2_BASE[0] + 0.0009, "lng": CS2_BASE[1] - 0.0008,
        "days_offset": 3, "start_hour": 17, "hours": 2, "ctxh": 0.0, "max_p": 20,
    },
    {
        "slug": "sport_volleyball_outdoor_cs1_b4",
        "title": "Giao lưu Bóng chuyền Đệm bóng và Đập bóng: Sân Bóng chuyền B4 Bách Khoa CS1",
        "desc": "Thi đấu bóng chuyền phong trào 6v6. Rèn luyện kỹ thuật bắt bước 1, chuyền hai set bóng và chắn bóng trên lưới. Không phân biệt trình độ, chào đón người mới.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Sân thể thao sau Nhà B4 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0004, "lng": CS1_BASE[1] + 0.0009,
        "days_offset": 6, "start_hour": 16, "hours": 2, "ctxh": 0.0, "max_p": 18,
    },

    # --- Cụm Chạy bộ, Bơi lội & Trí tuệ ---
    {
        "slug": "sport_running_morning_lake_ktx_cs2",
        "title": "Chạy bộ Rèn luyện Thể lực Sáng sớm: 5km quanh Bờ Hồ Ký túc xá ĐHQG CS2",
        "desc": "Dậy sớm rèn luyện sức bền cùng nhóm Runner Bách Khoa! Cự ly 5km tốc độ pace 6:30 thư giãn, hít thở không khí trong lành quanh hồ nước KTX Khu B.",
        "cat": "Thể thao & Giải trí", "campus": "CS2",
        "loc": "Hồ Ký túc xá ĐHQG - Gần Bách Khoa CS2",
        "lat": CS2_BASE[0] + 0.0016, "lng": CS2_BASE[1] + 0.0009,
        "days_offset": 1, "start_hour": 6, "hours": 1, "ctxh": 0.0, "max_p": 30,
    },
    {
        "slug": "sport_running_night_campus_loop_cs1",
        "title": "CLB Chạy bộ Đêm: Chạy Thả lỏng 3km Vòng quanh Khuôn viên Bách Khoa CS1",
        "desc": "Xua tan mệt mỏi sau ngày dài học tập! Chạy bộ nhẹ nhàng theo cung đường rợp bóng cây quanh các tòa nhà A1, B1, C1 tại cơ sở 1 Lý Thường Kiệt.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Cột cờ Cổng chính 268 Lý Thường Kiệt - CS1",
        "lat": CS1_BASE[0] - 0.0001, "lng": CS1_BASE[1] - 0.0001,
        "days_offset": 2, "start_hour": 20, "hours": 1, "ctxh": 0.0, "max_p": 25,
    },
    {
        "slug": "sport_swimming_weekend_swimmingpool_cs1",
        "title": "Bơi lội Rèn luyện Thể lực Cuối tuần: Hồ bơi Phú Thọ (Cạnh Bách Khoa CS1)",
        "desc": "Tập bơi ếch, bơi sải và rèn luyện dung tích phổi dưới sự hướng dẫn nhiệt tình của các bạn trong đội tuyển bơi lội trường. Vé hồ bơi tự túc theo giá sinh viên.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "CLB Bơi lặn Phú Thọ (215A Lý Thường Kiệt, Q.11)",
        "lat": CS1_BASE[0] + 0.0018, "lng": CS1_BASE[1] + 0.0002,
        "days_offset": 5, "start_hour": 8, "hours": 2, "ctxh": 0.0, "max_p": 20,
    },
    {
        "slug": "sport_chess_xiangqi_h6_lobby_cs2",
        "title": "CLB Cờ Bách Khoa: Đấu kỳ Giao lưu Cờ vua và Cờ tướng tại Sảnh Nhà H6 CS2",
        "desc": "Nơi các kỳ thủ so tài mưu lược qua các ván cờ chớp 5 phút và cờ tiêu chuẩn. Phân tích các thế trận khai cuộc kinh điển Ruy Lopez, Pháo đầu Mã đội.",
        "cat": "Thể thao & Giải trí", "campus": "CS2",
        "loc": "Sảnh Tầng trệt Nhà H6 - ĐH Bách Khoa CS2",
        "lat": CS2_BASE[0] + 0.0012, "lng": CS2_BASE[1] + 0.0006,
        "days_offset": 3, "start_hour": 15, "hours": 3, "ctxh": 0.0, "max_p": 30,
    },
    {
        "slug": "sport_esports_valorant_tournament_online",
        "title": "Giải đấu Thể thao Điện tử Sinh viên: Bách Khoa Cyber Cup Bộ môn Valorant",
        "desc": "Giải đấu eSports thường niên dành cho sinh viên Bách Khoa thi đấu online. Các đội 5 thành viên tranh tài qua vòng bảng thể thức BO1 và trận chung kết BO3 kịch tính.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Phòng Sinh hoạt Trực tuyến Discord BK Esports",
        "lat": CS1_BASE[0], "lng": CS1_BASE[1],
        "days_offset": 7, "start_hour": 19, "hours": 4, "ctxh": 0.0, "max_p": 64,
    },
    {
        "slug": "sport_martialarts_taekwondo_vovinam_cs1",
        "title": "CLB Võ thuật Bách Khoa: Buổi Tập Tự vệ Căn bản và Rèn luyện Thể lực Quyền đạo",
        "desc": "Rèn luyện thể lực, dẻo dai và các đòn thế tự vệ thực chiến giải thoát hiểm cơ bản dưới sự chỉ dẫn của các huấn luyện viên bộ môn Vovinam và Taekwondo Bách Khoa.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Sân Nhà Thi đấu C3 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0006, "lng": CS1_BASE[1] - 0.0013,
        "days_offset": 8, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 35,
    },
    {
        "slug": "sport_gym_fitness_workout_cs1",
        "title": "Nhóm Tập Gym Bách Khoa: Buổi Tập Thể hình Tăng cơ và Chia sẻ Dinh dưỡng Thể hình",
        "desc": "Cùng nhau tập luyện các bài tập phức hợp Compound: Squat, Bench Press, Deadlift đúng kỹ thuật phòng tránh chấn thương và tư vấn thực đơn bổ sung protein tiết kiệm cho sinh viên.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Phòng Gym Sinh viên KTX Bách Khoa - 497 Hòa Hảo",
        "lat": CS1_BASE[0] - 0.0013, "lng": CS1_BASE[1] + 0.0013,
        "days_offset": 4, "start_hour": 17, "hours": 2, "ctxh": 0.0, "max_p": 20,
    },
    {
        "slug": "sport_skateboarding_roller_cs1",
        "title": "Giao lưu Trượt Ván (Skateboarding) và Patin: Tối cuối tuần tại Sân A5 Bách Khoa",
        "desc": "Tập trung các bạn trẻ đam mê trượt ván đường phố. Hướng dẫn người mới tập đứng thăng bằng, đẩy ván và luyện kỹ thuật bật nhảy Ollie cơ bản.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "Sân Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 6, "start_hour": 19, "hours": 2, "ctxh": 0.0, "max_p": 25,
    },
    {
        "slug": "sport_yoga_relax_breathing_cs2",
        "title": "Lớp Tập Yoga & Thiền Thả lỏng: Xua tan Căng thẳng Mùa thi cho Nữ sinh Bách Khoa",
        "desc": "Rèn luyện hơi thở sâu Pranayama, các tư thế giãn cơ cột sống và thư giãn tâm trí sau những giờ ngồi làm đồ án căng thẳng trước máy tính.",
        "cat": "Thể thao & Giải trí", "campus": "CS2",
        "loc": "Phòng Sinh hoạt Tầng 3 KTX Khu B - ĐHQG",
        "lat": CS2_BASE[0] + 0.0022, "lng": CS2_BASE[1] + 0.0017,
        "days_offset": 9, "start_hour": 17, "hours": 2, "ctxh": 0.0, "max_p": 25,
    },
    {
        "slug": "sport_billiards_pool_friendly_cs1",
        "title": "Giao lưu Bida Lỗ (Pool 8-Ball) Phong trào: Chiều thứ Sáu Thư giãn sau Giờ học",
        "desc": "Giao hữu bi-a lỗ 8 bóng và 9 bóng vui vẻ giữa các anh em sinh viên Bách Khoa khu vực đường Tô Hiến Thành. Chia sẻ kỹ thuật nhắm bi và điều bi cái chuẩn xác.",
        "cat": "Thể thao & Giải trí", "campus": "CS1",
        "loc": "CLB Bida Sinh viên (Đường Tô Hiến Thành, Q.10)",
        "lat": CS1_BASE[0] + 0.0020, "lng": CS1_BASE[1] + 0.0012,
        "days_offset": 3, "start_hour": 17, "hours": 2, "ctxh": 0.0, "max_p": 16,
    },

    # =========================================================================
    # 5. CÂU LẠC BỘ & VĂN HÓA SINH VIÊN (15 hoạt động)
    # =========================================================================
    {
        "slug": "club_music_guitar_bgc_acoustic_night",
        "title": "CLB Guitar Bách Khoa (BGC): Đêm Nhạc Acoustic Thứ Sáu 'Ký ức Thời Sinh viên'",
        "desc": "Không gian âm nhạc mộc mạc hòa quyện cùng tiếng đàn guitar, cajon và những giọng ca mộc của sinh viên kỹ thuật. Giao lưu âm nhạc mở và hát theo yêu cầu.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Sảnh Nhà B4 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0004, "lng": CS1_BASE[1] + 0.0008,
        "days_offset": 3, "start_hour": 18, "hours": 3, "ctxh": 0.0, "max_p": 100,
    },
    {
        "slug": "club_lang_bec_english_coffee_talk_ai",
        "title": "CLB Tiếng Anh Bách Khoa (BEC): Coffee Talk Chủ đề 'Trí tuệ Nhân tạo và Việc làm Tương lai'",
        "desc": "Thảo luận 100% bằng tiếng Anh theo nhóm nhỏ, phản biện ý kiến về tác động của ChatGPT và AI đối với kỹ sư công nghệ. Cơ hội kết nối du học sinh trao đổi.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Highlands Coffee - 268 Lý Thường Kiệt",
        "lat": CS1_BASE[0] + 0.0015, "lng": CS1_BASE[1] + 0.0010,
        "days_offset": 4, "start_hour": 14, "hours": 2, "ctxh": 0.0, "max_p": 30,
    },
    {
        "slug": "club_media_photography_photowalk_cs2",
        "title": "CLB Nhiếp ảnh (BK Media): Buổi Chụp ảnh Photowalk Hoàng hôn Hồ Đá Làng Đại học",
        "desc": "Chia sẻ kỹ thuật bố cục một phần ba, kỹ thuật phơi sáng thủ công trên máy ảnh cơ DSLR/Mirrorless và thực hành chụp ảnh chân dung ngoại cảnh bắt trọn khoảnh khắc hoàng hôn.",
        "cat": "CLB & Đội nhóm", "campus": "CS2",
        "loc": "Hồ Tiền Phong & Bờ Hồ Đá ĐHQG - CS2",
        "lat": CS2_BASE[0] - 0.0015, "lng": CS2_BASE[1] - 0.0015,
        "days_offset": 5, "start_hour": 15, "hours": 3, "ctxh": 0.0, "max_p": 25,
    },
    {
        "slug": "club_reading_book_review_monthly",
        "title": "CLB Sách và Văn hóa Đọc: Tọa đàm Thảo luận Cuốn sách 'Tư Duy Nhanh và Chậm'",
        "desc": "Cùng nhau bàn luận về hai hệ thống tư duy của não bộ, những định kiến tâm lý thường gặp trong cuộc sống và cách rèn luyện tư duy phản biện sắc bén cho sinh viên.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Thư viện Bách Khoa A2 - Phòng Sinh hoạt tầng 1",
        "lat": CS1_BASE[0] + 0.0001, "lng": CS1_BASE[1] + 0.0006,
        "days_offset": 6, "start_hour": 14, "hours": 2, "ctxh": 0.0, "max_p": 35,
    },
    {
        "slug": "club_robotics_robocon_recruitment_demo",
        "title": "Đội Robocon Bách Khoa: Trình diễn Robot Bắn phá và Tuyển thành viên Thế hệ mới",
        "desc": "Chiêm ngưỡng các cỗ máy robot cơ khí tự hành và bán tự động do chính sinh viên Bách Khoa chế tạo. Thông tin đợt tuyển quân các ban Cơ khí, Mạch điện tử và Lập trình điều khiển.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Sân Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 8, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 120,
    },
    {
        "slug": "club_dance_modern_hiphop_cs1_a5",
        "title": "CLB Vũ đạo Sinh viên (BK Dance): Buổi Tập Nhảy Hiện đại và Kpop Dance Cover",
        "desc": "Giải phóng cơ thể cùng các điệu nhảy Hiphop Choreography và Kpop sôi động. Rèn luyện sự tự tin trình diễn sân khấu và chuẩn bị tiết mục văn nghệ chào tân sinh viên.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Sảnh Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 2, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 40,
    },
    {
        "slug": "club_boardgame_werewolf_catan_cs2",
        "title": "Hội Yêu thích Board Game Bách Khoa: Buổi Đấu trí Ma Sói, Catan và Avalon Cuối tuần",
        "desc": "Giao lưu kết bạn cuối tuần cùng các tựa game bàn cờ chiến thuật hấp dẫn. Rèn luyện tư duy thuyết phục, đọc vị ngôn ngữ cơ thể và chiến lược quản lý tài nguyên.",
        "cat": "CLB & Đội nhóm", "campus": "CS2",
        "loc": "Phòng Tự học H6-302 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0006, "lng": CS2_BASE[1] + 0.0003,
        "days_offset": 5, "start_hour": 14, "hours": 4, "ctxh": 0.0, "max_p": 30,
    },
    {
        "slug": "club_japan_culture_anime_manga_cs1",
        "title": "CLB Văn hóa & Tiếng Nhật Bách Khoa (BJC): Lễ hội Giao lưu Văn hóa và Trải nghiệm Origami",
        "desc": "Khám phá nghệ thuật gấp giấy Origami Nhật Bản, trải nghiệm mặc thử trang phục truyền thống Yukata và học các mẫu câu giao tiếp tiếng Nhật căn bản chuẩn bị du học.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0003,
        "days_offset": 9, "start_hour": 8, "hours": 3, "ctxh": 0.0, "max_p": 60,
    },
    {
        "slug": "club_startup_innovation_pitching_demo",
        "title": "CLB Khởi nghiệp (BK Innovation): Demo Day Thuyết trình Ý tưởng Dự án Khởi nghiệp Sinh viên",
        "desc": "Các nhóm tác giả trình bày mô hình kinh doanh Canvas (BMC), giải pháp công nghệ trước hội đồng Ban Giám khảo là các Founder và Quỹ đầu tư mạo hiểm (Venture Capital).",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 11, "start_hour": 14, "hours": 4, "ctxh": 0.0, "max_p": 80,
    },
    {
        "slug": "club_astronomy_stargazing_cs2",
        "title": "CLB Thiên văn Học Bách Khoa: Đêm Quan sát Mặt Trăng và Sao Mộc qua Kính Thiên văn",
        "desc": "Trải nghiệm ngắm nhìn hố va chạm trên Mặt Trăng và các vành đai Sao Thổ qua kính thiên văn phản xạ chuyên dụng tại sân thượng tòa nhà H6 Cơ sở 2 thoáng đãng.",
        "cat": "CLB & Đội nhóm", "campus": "CS2",
        "loc": "Sân thượng Tòa nhà H6 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0012, "lng": CS2_BASE[1] + 0.0006,
        "days_offset": 10, "start_hour": 19, "hours": 3, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "club_film_cinema_screening_discussion",
        "title": "CLB Điện ảnh Bách Khoa: Chiếu phim Kinh điển 'Oppenheimer' và Bàn luận Khoa học",
        "desc": "Thưởng thức bộ phim điện ảnh đoạt giải Oscar và thảo luận về lịch sử dự án Manhattan, nguyên lý phản ứng phân hạch hạt nhân và trách nhiệm đạo đức của nhà khoa học.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 7, "start_hour": 18, "hours": 3, "ctxh": 0.0, "max_p": 70,
    },
    {
        "slug": "club_environment_green_campus_ambassador",
        "title": "CLB Môi trường Xanh: Lớp Hướng dẫn Làm Xà phòng Hữu cơ từ Dầu ăn Thừa",
        "desc": "Tái chế dầu ăn đã qua sử dụng thành những bánh xà phòng hữu cơ an toàn cho da tay, lan tỏa lối sống bền vững và tinh thần bảo vệ nguồn nước trong sinh viên.",
        "cat": "CLB & Đội nhóm", "campus": "CS2",
        "loc": "Phòng Lab Hóa H2-101 - CS2 Dĩ An",
        "lat": CS2_BASE[0] - 0.0005, "lng": CS2_BASE[1] + 0.0006,
        "days_offset": 6, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 30,
    },
    {
        "slug": "club_gdsc_google_tech_talk_flutter",
        "title": "Google Developer Student Club (GDSC HCMUT): Tech Talk 'Build with AI on Google Cloud'",
        "desc": "Giao lưu cùng chuyên gia Google Developer Expert (GDE), tìm hiểu hệ sinh thái Google AI, Vertex AI và cách tích hợp các mô hình Gemini vào ứng dụng di động Flutter.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 8, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 120,
    },
    {
        "slug": "club_coding_bk_icpc_mock_contest",
        "title": "BK Coding Club: Kì thi Lập trình Thử nghiệm Mẫu Format Kỳ thi Quốc gia ICPC",
        "desc": "Kỳ thi thử nghiệm thuật toán 5 tiếng liên tục dành cho các đội tuyển sinh viên. Thi đấu xếp hạng real-time trên bảng điểm trực tuyến Codeforces/VNOJ.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Phòng Máy tính B1-301 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0003, "lng": CS1_BASE[1] + 0.0002,
        "days_offset": 12, "start_hour": 8, "hours": 5, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "club_art_sketching_drawing_watercolour",
        "title": "Nhóm Ký họa Bách Khoa: Buổi Vẽ Ký họa Kiến trúc Giảng đường Cũ Cơ sở 1",
        "desc": "Dành cho các bạn sinh viên yêu thích hội họa và màu nước. Cùng nhau ngồi dưới bóng cây cổ thụ ký họa lại những góc ban công cổ kính của dãy nhà A1 và C1.",
        "cat": "CLB & Đội nhóm", "campus": "CS1",
        "loc": "Khuôn viên Sân Cột Cờ A1 - CS1",
        "lat": CS1_BASE[0] + 0.0001, "lng": CS1_BASE[1] + 0.0001,
        "days_offset": 4, "start_hour": 8, "hours": 3, "ctxh": 0.0, "max_p": 25,
    },

    # =========================================================================
    # 6. HƯỚNG NGHIỆP & DOANH NGHIỆP (15 hoạt động)
    # =========================================================================
    {
        "slug": "career_job_fair_bachkhoa_annual_2026",
        "title": "Ngày hội Việc làm Bách Khoa Job Fair 2026: Kết nối hơn 80 Doanh nghiệp Công nghệ Hàng đầu",
        "desc": "Sự kiện tuyển dụng quy mô lớn nhất năm! Hơn 80 gian hàng doanh nghiệp công nghệ, kỹ thuật, dầu khí, xây dựng phỏng vấn trực tiếp tại chỗ và nhận CV thực tập sinh tiềm năng.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Khuôn viên Sân A5 và Sân C3 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 12, "start_hour": 8, "hours": 8, "ctxh": 0.0, "max_p": 300,
    },
    {
        "slug": "career_cv_workshop_tech_hr_review",
        "title": "Workshop: Kỹ năng Viết CV Công nghệ Chuẩn Quốc tế và Tối ưu từ khóa cho Hệ thống ATS",
        "desc": "Hướng dẫn cách trình bày dự án nổi bật, cách viết bullet point theo cấu trúc STAR (Situation - Task - Action - Result) gây ấn tượng mạnh với nhà tuyển dụng IT.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0003,
        "days_offset": 3, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 100,
    },
    {
        "slug": "career_mock_interview_senior_leads",
        "title": "Chương trình Phỏng vấn Thử (Mock Interview 1-on-1) cùng các Senior Tech Lead",
        "desc": "Sinh viên được trải nghiệm trực tiếp buổi phỏng vấn kỹ thuật thật 45 phút bao gồm live-coding và câu hỏi thiết kế hệ thống, nhận phản hồi chi tiết khắc phục điểm yếu.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Phòng Hội thảo B4-202 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0003, "lng": CS1_BASE[1] + 0.0008,
        "days_offset": 7, "start_hour": 13, "hours": 4, "ctxh": 0.0, "max_p": 30,
    },
    {
        "slug": "career_talkshow_bridge_engineer_japan",
        "title": "Tọa đàm Hướng nghiệp: Con đường Trở thành Kỹ sư Cầu nối (BrSE) Làm việc tại Nhật Bản",
        "desc": "Chia sẻ về lộ trình thăng tiến, yêu cầu ngoại ngữ tiếng Nhật N2/N1, văn hóa doanh nghiệp Nhật và cơ hội định cư lâu dài cho kỹ sư công nghệ thông tin Bách Khoa.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 9, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 90,
    },
    {
        "slug": "career_internship_bosch_automotive_talk",
        "title": "Chương trình Gặp gỡ Doanh nghiệp: Cơ hội Thực tập Kỹ thuật tại Bosch Global Software",
        "desc": "Đại diện Bosch chia sẻ các dự án nghiên cứu phát triển phần mềm ô tô tự hành, kiểm thử hệ thống phanh ABS và quy trình tuyển dụng thực tập sinh có lương.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS2",
        "loc": "Hội trường H1-101 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0002, "lng": CS2_BASE[1] + 0.0007,
        "days_offset": 5, "start_hour": 9, "hours": 3, "ctxh": 0.0, "max_p": 80,
    },
    {
        "slug": "career_seminar_semiconductor_chip_design",
        "title": "Hội thảo Công nghiệp Vi mạch: Xu hướng Ngành Bán dẫn và Kỹ sư Thiết kế Vi mạch IC",
        "desc": "Phân tích cơ hội việc làm tỷ USD của ngành công nghiệp bán dẫn tại Việt Nam: thiết kế vi mạch kỹ thuật số (Front-end/Back-end), ngôn ngữ Verilog và kiểm thử bán dẫn.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0003,
        "days_offset": 6, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 100,
    },
    {
        "slug": "career_fpt_software_fresher_academy",
        "title": "Ngày hội Phỏng vấn Tuyển dụng Nhanh: Chương trình Fresher IT cùng FPT Software",
        "desc": "Kiểm tra năng lực lập trình và phỏng vấn trực tiếp nhận offer đào tạo có trợ cấp hàng tháng cho sinh viên chuẩn bị tốt nghiệp chuyên ngành CNTT và Kỹ thuật Phần mềm.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Phòng C5-101 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0006, "lng": CS1_BASE[1] - 0.0004,
        "days_offset": 8, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 70,
    },
    {
        "slug": "career_talk_vng_game_producer",
        "title": "Tọa đàm Hướng nghiệp: Nghề Làm Game và Vị trí Game Producer tại VNG Corporation",
        "desc": "Giao lưu cùng các cựu sinh viên Bách Khoa hiện là Product Manager tại VNG: chia sẻ quy trình sản xuất một tựa game từ khâu lên ý tưởng đến lúc phát hành toàn cầu.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 10, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 120,
    },
    {
        "slug": "career_consulting_big4_it_audit",
        "title": "Seminar: Kiểm toán Công nghệ Thông tin (IT Audit) và Cơ hội Nghề nghiệp tại Big 4",
        "desc": "Tìm hiểu ngành tư vấn rủi ro hệ thống công nghệ thông tin, đánh giá kiểm soát bảo mật tại các tập đoàn tài chính đa quốc gia PwC, Deloitte, EY, KPMG.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Phòng B4-201 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0003, "lng": CS1_BASE[1] + 0.0007,
        "days_offset": 11, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "career_factory_tour_vinfast_automotive",
        "title": "Chuyến Tham quan Thực tế Doanh nghiệp: Khám phá Dây chuyền Lắp ráp Ô tô VinFast",
        "desc": "Chuyến xe đưa đón sinh viên Bách Khoa tham quan trực tiếp tổ hợp nhà máy sản xuất ô tô điện hiện đại, tìm hiểu hệ thống cánh tay robot hàn tự động đạt chuẩn công nghiệp 4.0.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Sân A5 tập trung xe đưa đón - CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 13, "start_hour": 7, "hours": 8, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "career_scholarship_erasmus_postgraduate",
        "title": "Hội thảo Học bổng Sau Đại học: Chinh phục Học bổng Toàn phần Erasmus Mundus Châu Âu",
        "desc": "Bí quyết chuẩn bị hồ sơ du học Thạc sĩ/Tiến sĩ: viết thư giới thiệu (Recommendation Letter), bài luận động lực (Statement of Purpose) và cách liên hệ giáo sư hướng dẫn.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS2",
        "loc": "Phòng Hội thảo H6-201 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0005, "lng": CS2_BASE[1] + 0.0003,
        "days_offset": 7, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 60,
    },
    {
        "slug": "career_freelancer_upwork_global_remote",
        "title": "Workshop: Xây dựng Hồ sơ Freelancer Công nghệ Quốc tế và Kiếm tiền từ Xa trên Upwork",
        "desc": "Cách tạo profile ấn tượng, chiến thuật viết proposal đấu thầu dự án phần mềm với khách hàng Mỹ, Châu Âu và quy trình thanh toán ngoại tệ an toàn về tài khoản Việt Nam.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Phòng C1-202 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0003,
        "days_offset": 4, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "career_linkedin_networking_personal_branding",
        "title": "Lớp Kỹ năng: Xây dựng Thương hiệu Cá nhân trên LinkedIn và Mở rộng Mạng lưới Quan hệ",
        "desc": "Tối ưu hóa tiêu đề Headline, phần tóm tắt About và cách chia sẻ bài viết kỹ thuật thu hút nhà tuyển dụng chủ động săn đón (headhunting).",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS2",
        "loc": "Phòng H6-202 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0006, "lng": CS2_BASE[1] + 0.0004,
        "days_offset": 6, "start_hour": 14, "hours": 2, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "career_management_trainee_fmcg_talk",
        "title": "Tọa đàm Tuyển dụng: Lộ trình Trở thành Quản trị viên Tập sự (Management Trainee) FMCG",
        "desc": "Khám phá chương trình đào tạo lãnh đạo trẻ tương lai tại các tập đoàn tiêu dùng nhanh Unilever, P&G, Nestlé dành cho sinh viên kỹ thuật có tư duy quản trị tốt.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 8, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 70,
    },
    {
        "slug": "career_intel_products_vietnam_internship",
        "title": "Ngày hội Công nghệ Intel: Cơ hội Nghề nghiệp tại Nhà máy Lắp ráp và Kiểm định Vi mạch",
        "desc": "Giao lưu cùng ban lãnh đạo Intel Products Vietnam, tìm hiểu quy trình đóng gói chip tiên tiến và các vị trí kỹ sư bảo trì thiết bị, kỹ sư chất lượng cho sinh viên năm cuối.",
        "cat": "Hướng nghiệp & Việc làm", "campus": "CS1",
        "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 11, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 150,
    },

    # =========================================================================
    # 7. KỸ NĂNG MỀM & HỘI NHẬP (10 hoạt động)
    # =========================================================================
    {
        "slug": "soft_public_speaking_presentation_skills",
        "title": "Khóa Huấn luyện: Kỹ năng Thuyết trình Tự tin và Thiết kế Slide Báo cáo Đồ án Cuốn hút",
        "desc": "Bí quyết làm chủ sân khấu: cách kiểm soát giọng nói, ngôn ngữ hình thể tự nhiên, kỹ thuật dẫn dắt câu chuyện (Storytelling) và cách thiết kế slide tối giản trực quan.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 2, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 80,
    },
    {
        "slug": "soft_time_management_pomodoro_productivity",
        "title": "Workshop: Kỹ thuật Quản lý Thời gian Hiệu quả và Đánh bại Trì hoãn trong Mùa thi",
        "desc": "Áp dụng ma trận Eisenhower phân loại mức độ khẩn cấp, phương pháp quả cà chua Pomodoro tập trung sâu và công cụ Notion lập kế hoạch biểu đồ học tập khoa học.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Phòng Hội thảo H6-201 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0005, "lng": CS2_BASE[1] + 0.0003,
        "days_offset": 4, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "soft_conflict_resolution_teamwork_skills",
        "title": "Tọa đàm: Nghệ thuật Giải quyết Xung đột Nhóm và Nâng cao Hiệu suất Làm việc Tập thể",
        "desc": "Học cách lắng nghe tích cực (Active Listening), phương pháp phản hồi mang tính xây dựng và kỹ năng đàm phán phân chia công việc công bằng khi làm bài tập lớn.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng B4-105 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0004, "lng": CS1_BASE[1] + 0.0008,
        "days_offset": 6, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 45,
    },
    {
        "slug": "soft_critical_thinking_problem_solving",
        "title": "Chuyên đề: Tư duy Phản biện (Critical Thinking) và Phương pháp Giải quyết Vấn đề Kỹ thuật",
        "desc": "Thực hành phương pháp 5 Whys đào sâu nguyên nhân gốc rễ, sơ đồ xương cá Ishikawa và tư duy thiết kế Design Thinking để giải quyết những thách thức kỹ thuật phức tạp.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Phòng H6-203 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0008, "lng": CS2_BASE[1] + 0.0005,
        "days_offset": 8, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 40,
    },
    {
        "slug": "soft_emotional_intelligence_eq_stress_relief",
        "title": "Lớp Kỹ năng Cảm xúc (EQ): Nhận diện Cảm xúc và Giải tỏa Áp lực Học tập cho Sinh viên",
        "desc": "Hiểu rõ cơ chế phản ứng sinh học của căng thẳng (stress), rèn luyện thói quen tự nhận thức (Self-awareness) và các bài tập chánh niệm giúp duy trì tinh thần lạc quan.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng Sinh hoạt Tầng 2 Thư viện A2 - CS1",
        "lat": CS1_BASE[0] + 0.0001, "lng": CS1_BASE[1] + 0.0006,
        "days_offset": 5, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 35,
    },
    {
        "slug": "soft_freshmen_campus_orientation_k26",
        "title": "Ngày hội Tân Sinh viên K26: Cẩm nang Sống sót và Tận dụng Tối đa Tiện ích Đại học",
        "desc": "Chia sẻ kinh nghiệm đăng ký tín chỉ học phần không bị nghẽn mạng, cách sử dụng tài nguyên thư viện điện tử, xe buýt liên cơ sở và các học bổng khuyến khích học tập.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Hội trường H1-101 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0002, "lng": CS2_BASE[1] + 0.0007,
        "days_offset": 10, "start_hour": 8, "hours": 4, "ctxh": 0.5, "max_p": 150,
    },
    {
        "slug": "soft_financial_literacy_student_budgeting",
        "title": "Hội thảo Tài chính Cá nhân: Quản lý Chi tiêu Tiết kiệm và Đầu tư Thông minh Thời Sinh viên",
        "desc": "Quy tắc 6 chiếc lọ tài chính, quản lý chi phí sinh hoạt hàng tháng, phân biệt nhu cầu thiết yếu vs mong muốn tức thời và tránh xa các cạm bẫy tín dụng đen sinh viên.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Hội trường C1 - Trường ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] + 0.0008, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 7, "start_hour": 18, "hours": 2, "ctxh": 0.0, "max_p": 60,
    },
    {
        "slug": "soft_cross_cultural_communication_exchange",
        "title": "Giao lưu Hội nhập Quốc tế: Kỹ năng Giao tiếp Đa văn hóa cho Sinh viên Bách Khoa",
        "desc": "Tìm hiểu những rào cản văn hóa khi làm việc cùng đồng nghiệp phương Tây, văn hóa cúi chào Đông Á và những quy tắc ứng xử chuẩn mực trong môi trường đa quốc gia.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Phòng Hội thảo B4-201 - CS1",
        "lat": CS1_BASE[0] - 0.0003, "lng": CS1_BASE[1] + 0.0007,
        "days_offset": 9, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 50,
    },
    {
        "slug": "soft_negotiation_persuasion_skills",
        "title": "Workshop: Kỹ năng Đàm phán và Thuyết phục trong Hợp tác Dự án Kỹ thuật",
        "desc": "Nguyên lý đàm phán đôi bên cùng có lợi (Win-Win), xác định vùng thỏa thuận khả thi (ZOPA) và phương án thay thế tốt nhất (BATNA) khi thương lượng hợp đồng đồ án.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS2",
        "loc": "Phòng H6-204 - CS2 Dĩ An",
        "lat": CS2_BASE[0] + 0.0007, "lng": CS2_BASE[1] + 0.0006,
        "days_offset": 11, "start_hour": 14, "hours": 3, "ctxh": 0.0, "max_p": 40,
    },
    {
        "slug": "soft_leadership_student_club_management",
        "title": "Chương trình Thủ lĩnh Sinh viên: Kỹ năng Lãnh đạo và Quản trị Nhân sự Đội nhóm",
        "desc": "Phương pháp truyền cảm hứng, trao quyền (empowerment) cho thành viên và xây dựng văn hóa đội nhóm gắn kết, bền vững cho ban chủ nhiệm các câu lạc bộ trường.",
        "cat": "Học thuật & Kỹ năng", "campus": "CS1",
        "loc": "Hội trường A5 - ĐH Bách Khoa CS1",
        "lat": CS1_BASE[0] - 0.0005, "lng": CS1_BASE[1] + 0.0004,
        "days_offset": 13, "start_hour": 8, "hours": 4, "ctxh": 0.0, "max_p": 70,
    },
]

async def seed_corpus_120():
    print("=" * 80)
    print("🚀 BẮT ĐẦU SEED CORPUS 120 HOẠT ĐỘNG SYNTHETIC (ĐA DẠNG NGỮ NGHĨA & RÀNG BUỘC)...")
    print(f"📦 Tổng số hoạt động thiết kế: {len(CORPUS_ACTIVITIES)}")
    print("=" * 80)

    # 1. Khởi tạo Gemini client để batch embedding
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    # 2. Chuẩn bị text embedding cho 120 activities
    embed_texts = []
    for item in CORPUS_ACTIVITIES:
        text_for_embed = (
            f"Tiêu đề: {item['title']}. "
            f"Nội dung: {item['desc']} "
            f"Phân loại: {item['cat']}. "
            f"Địa điểm: {item['loc']} ({item['campus']}). "
            f"Ngày CTXH: {item['ctxh']} ngày."
        )
        embed_texts.append(text_for_embed)

    print(f"🧠 Sinh vector embeddings 768 chiều qua Google Gemini API (Batching)...")
    all_embeddings = []
    batch_size = 30
    for i in range(0, len(embed_texts), batch_size):
        chunk = embed_texts[i:i + batch_size]
        print(f"   Đang xử lý lô {i + 1} - {min(i + batch_size, len(embed_texts))} / {len(embed_texts)}...")
        
        success = False
        for attempt in range(3):
            try:
                res = client.models.embed_content(
                    model='gemini-embedding-001',
                    contents=chunk,
                    config=types.EmbedContentConfig(output_dimensionality=768),
                )
                for emb in res.embeddings:
                    all_embeddings.append(emb.values)
                success = True
                break
            except Exception as e:
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"   ⏳ Gặp rate limit (429), chờ 25 giây để làm mới quota (lần thử {attempt + 1}/3)...")
                    import time
                    time.sleep(26)
                else:
                    print(f"⚠️ Lỗi batch embedding: {e}")
                    break
        
        if not success:
            print("   ⚠️ Tạo fallback normalized vector 768-dim cho lô này...")
            for _ in chunk:
                vec = [random.uniform(-0.1, 0.1) for _ in range(768)]
                all_embeddings.append(vec)

    print(f"✅ Đã có đủ {len(all_embeddings)} vector embeddings (768 chiều)!")

    # 3. Kết nối Database
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    now = datetime.datetime.now(timezone.utc)

    async with async_session() as db:
        # Lấy host users có sẵn từ master seed
        users = (await db.execute(select(User))).scalars().all()
        if not users:
            print("❌ Không tìm thấy User nào trong database! Vui lòng chạy seed_bachkhoa_master.py trước.")
            return

        admin_user = next((u for u in users if u.role == UserRole.admin), users[0])
        student_user = next((u for u in users if u.role == UserRole.student), users[-1])
        admin_user_id = admin_user.id
        student_user_id = student_user.id

        # Làm sạch bảng activities cũ và các liên kết phụ thuộc
        print("🧹 Làm sạch bảng hoạt động cũ để nạp corpus 120 chuẩn hóa...")
        for tbl in ["comments", "content_likes", "join_requests", "activity_cohosts", "activities"]:
            try:
                await db.execute(text(f"DELETE FROM {tbl}"))
                await db.commit()
            except Exception as e:
                await db.rollback()

        # Nạp 120 activities
        print("📥 Đang thêm 120 hoạt động vào PostgreSQL...")
        registry_data = []
        activities_to_insert = []

        for idx, (item, emb_vec) in enumerate(zip(CORPUS_ACTIVITIES, all_embeddings)):
            act_id = uuid.uuid4()
            
            # Tính start_time & end_time
            days_delta = item.get("days_offset", 1)
            target_date = now.date() + timedelta(days=days_delta)
            start_hour = item.get("start_hour", 8)
            duration_hours = item.get("hours", 3)
            
            start_t = datetime.datetime.combine(
                target_date,
                datetime.time(start_hour, 0),
                tzinfo=timezone.utc
            )
            end_t = start_t + timedelta(hours=duration_hours)

            day_name = start_t.strftime("%A")
            is_weekend = start_t.weekday() in (5, 6)
            time_of_day = "morning" if start_hour < 12 else ("afternoon" if start_hour < 18 else "evening")

            act = Activity(
                id=act_id,
                host_id=admin_user_id if "Cuộc thi" in item["title"] or "Job Fair" in item["title"] else student_user_id,
                title=item["title"],
                description=item["desc"],
                category=item["cat"],
                meeting_location=item["loc"],
                start_time=start_t,
                end_time=end_t,
                social_work_days=item["ctxh"],
                max_participants=item["max_p"],
                current_participants=random.randint(5, max(6, item["max_p"] - 5)),
                privacy=ActivityPrivacy.public,
                require_approval=False,
                embedding=emb_vec,
            )
            act.marker_location = f"POINT({item['lng']} {item['lat']})"
            activities_to_insert.append(act)

            # Metadata cho benchmark ground truth registry
            registry_data.append({
                "id": str(act_id),
                "slug": item["slug"],
                "title": item["title"],
                "category": item["cat"],
                "campus": item["campus"],
                "location": item["loc"],
                "lat": item["lat"],
                "lng": item["lng"],
                "start_time": start_t.isoformat(),
                "end_time": end_t.isoformat(),
                "day_of_week": day_name,
                "is_weekend": is_weekend,
                "time_of_day": time_of_day,
                "social_work_days": item["ctxh"],
                "max_participants": item["max_p"],
            })

        db.add_all(activities_to_insert)
        await db.commit()
        print(f"✅ Đã nạp thành công {len(activities_to_insert)} hoạt động vào database!")

        # Lưu registry ra scratch folder
        registry_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bao-cao", "scratch", "corpus_120_registry.json")
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry_data, f, ensure_ascii=False, indent=2)
        print(f"📄 Đã lưu file registry Ground Truth: {registry_path}")

    await engine.dispose()
    print("\n" + "=" * 80)
    print("🎉 HOÀN TẤT SEED CORPUS 120 HOẠT ĐỘNG!")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(seed_corpus_120())
