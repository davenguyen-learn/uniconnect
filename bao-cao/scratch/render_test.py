import plantuml

code = """@startuml
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Helvetica, Arial, sans-serif"
skinparam defaultFontSize 11
skinparam roundCorner 8
skinparam shadowing false
skinparam linetype ortho

skinparam rectangle {
    BorderThickness 1.2
    FontSize 11
}

rectangle "==TẦNG TRÌNH DIỄN (CLIENT / PRESENTATION LAYER)==\\n--\\n* **React 19 SPA (Vite + TypeScript + Tailwind CSS v4)**: Giao diện Web / Mobile Responsive\\n* **Bản đồ số tương tác (Leaflet)**: Tải và hiển thị mảnh bản đồ nền OpenStreetMap / CartoDB\\n* **HTML5 Geolocation API**: Thu thập tọa độ GPS và sai số accuracy phục vụ Geofencing\\n* **Dynamic QR Engine**: Hiển thị mã QR động Canvas/SVG và quét mã điểm danh" as L1 #E8F0FE

rectangle "==TẦNG CỔNG TIẾP NHẬN & ĐIỀU HƯỚNG (INGRESS & REVERSE PROXY)==\\n--\\n* **Nginx 1.27-alpine**: Tiếp nhận HTTPS (:443), giải mã TLS, điều hướng /api/* sang Uvicorn (:8000)\\n* **Bộ nhớ đệm tĩnh (Static Caching)**: Cache-Control: public, max-age=31536000, immutable cho /assets/*\\n* **Ranh giới bảo mật (Security Headers)**: X-Frame-Options DENY, X-Content-Type-Options nosniff\\n* **Chuyển tiếp định danh IP**: Thiết lập X-Real-IP, X-Forwarded-For vào mạng nội bộ Docker" as L2 #FFF3E0

rectangle "==TẦNG DỊCH VỤ ỨNG DỤNG (APPLICATION LAYER - FASTAPI MODULAR MONOLITH)==\\n--\\n**[1] Middleware & Ranh giới Bảo mật (Security Boundary)**\\n   • JWT Bearer Authenticator (Bcrypt, Access/Refresh Token)  • SlowAPI Rate Limiter  • RBAC & Co-host Guard\\n\\n**[2] Bộ điều phối API (API Routers)**\\n   • Auth & User Router   • Activity & Map Router   • Attendance Router (QR HMAC / GPS)\\n   • Calendar & ICS Router   • Groups & Co-host Router   • AI Chat & Admin Router\\n\\n**[3] Động cơ nghiệp vụ chuyên sâu (Core Business Engines)**\\n   • **Spatial Engine**: Xử lý tính toán không gian PostGIS (ST_DWithin, Bounding Box), GeoJSON\\n   • **Attendance Engine**: Sinh mã xoay động HMAC-SHA256 (30s) và Geofence Haversine Validator\\n   • **Smart Calendar Engine**: Thuật toán đối soát xung đột lịch [max(s) < min(e)] và xuất file .ics\\n   • **Gamification Engine**: Tự động tích lũy ngày CTXH và đối soát mở khóa danh hiệu (Trophies)\\n   • **AI Agent Orchestrator**: Điều phối ReAct Loop, Function Calling (3 Tools), Guardrails (max 3 turns)" as L3 #F3E5F5

rectangle "==TẦNG DỮ LIỆU & DỊCH VỤ NGOẠI VI (DATA & EXTERNAL SERVICES)==\\n--\\n**Cơ sở Dữ liệu Thống nhất (PostgreSQL 16 - AsyncPG Pool: 20 active / 10 overflow)**\\n  • **Relational Core**: Bảng Users, Activities, Participants, Groups, CoHosts, Trophies, ActivityLogs\\n  • **PostGIS Extension**: Kiểu dữ liệu GEOGRAPHY(Point, 4326), Chỉ mục không gian GIST\\n  • **pgvector Extension**: Cột embedding vector(768), Chỉ mục tìm kiếm tương đồng HNSW (Cosine)\\n\\n**Dịch vụ Đám mây Ngoại vi (External Cloud Services)**\\n  • **Google GenAI API**: Mô hình Gemini 2.5 Flash (suy luận gọi hàm) và gemini-embedding-001 (nhúng 768-d)\\n  • **Google OAuth 2.0**: Xác thực ủy quyền đăng nhập sinh viên SSO\\n  • **OpenStreetMap Tile Server**: Cung cấp lớp bản đồ nền qua CartoDB Positron / OSM HTTPS" as L4 #E8F5E9

L1 -down-> L2 : "HTTPS (:443) / REST API Requests"
L2 -down-> L3 : "Forward HTTP (:8000) qua Docker Network nội bộ"
L3 -down-> L4 : "Truy vấn CSDL (TCP :5432) & Gọi External Cloud APIs (HTTPS)"

@enduml"""

server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')
data = server.processes(code)
with open('scratch/test_arch_vertical.png', 'wb') as f:
    f.write(data)
print('Rendered test_arch_vertical.png successfully!')
