# UniConnect — Production Deployment & Operational Runbook

Tài liệu này chuẩn hóa toàn bộ hướng dẫn triển khai, giám sát, cấu hình hạ tầng và quy trình vận hành cho hệ sinh thái **UniConnect**.

---

## 1. Kiến trúc Triển khai (Deployment Topology)

```
[ Internet Client / Browser ]
           │
           ▼ (HTTPS / Port 443)
[ Edge Proxy: Cloudflare / AWS ALB / Ingress ]
    - SSL/TLS Termination
    - DDoS Mitigation
    - Forwards: X-Forwarded-For, X-Forwarded-Proto (https)
           │
           ▼ (HTTP / Port 80)
[ Ingress: Nginx Container (client) ]
    - Serves Static SPA Assets (Vite Distribution)
    - Immutable Cache for /assets/ (max-age=1y)
    - SPA Route Fallback (try_files $uri $uri/ /index.html)
    - Re-maps X-Forwarded-Proto
    - Reverse Proxy /api/ to server:8000
           │
           ▼ (HTTP / Docker Internal Bridge Network)
[ Backend: FastAPI Container (server) ]
    - Gunicorn (2+ Workers) + UvicornWorker
    - Non-root User (appuser: 1001)
    - ProxyHeadersMiddleware (validates TRUSTED_PROXY_IPS)
    - Bounded Memory Rate Limiting (10,000 ceiling)
    - RequestTimingMiddleware (X-Process-Time header)
           │
           ▼ (AsyncPG / Docker Internal Network)
[ Database: PostgreSQL 16 + PostGIS + pgvector (db) ]
    - Connection Pooling (Size: 20, Max Overflow: 10, Timeout: 30s)
    - pool_pre_ping=True, pool_recycle=1800s
    - Dedicated Persistent Volume: postgres_prod_data
```

---

## 2. Quy chuẩn Health Check Semantics (Liveness vs. Readiness)

Bộ cân bằng tải (Load Balancer / Ingress / Kubernetes Orchestrator) **phải phân biệt rõ ràng hai endpoint probe**:

| Endpoint | Giao thức | Phụ thuộc | Ngữ nghĩa Vận hành | Đề xuất Cấu hình Orchestration |
| :--- | :--- | :--- | :--- | :--- |
| `/health` | HTTP | Nginx | **Liveness Probe**: Xác nhận Nginx container còn sống và có thể phục vụ mã nguồn tĩnh của Single Page Application. | Dùng cho Nginx container restart policy. |
| `/api/health` | HTTP | FastAPI + PostgreSQL | **Readiness Probe**: Xác nhận FastAPI worker sẵn sàng và kết nối DB khả dụng (live ping `SELECT 1`). | Dùng cho Load Balancer định tuyến traffic hoặc Kubernetes Readiness Probe. |

> [!WARNING]
> **Không cấu hình Load Balancer chỉ probe `/health`**: Nếu chỉ probe `/health`, khi PostgreSQL hoặc FastAPI gặp sự cố, Load Balancer vẫn xem pod là "healthy" và tiếp tục chuyển tiếp traffic API vào upstream đang lỗi.

---

## 3. Chính sách Quyền Trình duyệt (Permissions-Policy & GPS Check-in)

Trong [client/nginx.conf](file:///c:/Users/Admin/Code/uniconnect-v2/client/nginx.conf), header `Permissions-Policy` được khóa như sau:

```nginx
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(self)" always;
```

- `camera=()`, `microphone=()`: Vô hiệu hóa truy cập phần cứng nhạy cảm nhằm bảo mật client-side.
- `geolocation=(self)`: **Bắt buộc cho phép trên cùng origin (self)** để phục vụ tính năng **GPS Check-in** (Phase 5) và tìm kiếm sự kiện lân cận (`discover_nearby`). Tuyệt đối không đổi thành `geolocation=()` vì sẽ làm tê liệt API `navigator.geolocation` của trình duyệt.

---

## 4. Operational Backlog: Quy trình Sao lưu & Phục hồi (Backup & DR)

Tính năng lưu trữ liên tục (Persistence) đã hoạt động qua volume `postgres_prod_data`. Công tác Sao lưu & Khắc phục thảm họa (Backup & Disaster Recovery) được quản lý như một **Operational Backlog (MEDIUM)** với các công cụ đã được đóng gói sẵn:

### 4.1. Tạo bản sao lưu định kỳ (Automated Backup)
Chạy script tự động (khuyến nghị thiết lập qua cron job hàng ngày vào 02:00 AM):
```bash
./scripts/backup_postgres.sh /var/backups/uniconnect
```
- Sử dụng `pg_dump --clean --if-exists` nén qua `gzip`.
- Tự động xóa các bản lưu cũ hơn 14 ngày (retention policy).

### 4.2. Phục hồi từ bản sao lưu (Restore Drill)
```bash
./scripts/restore_postgres.sh /var/backups/uniconnect/uniconnect_backup_YYYYMMDD_HHMMSS.sql.gz
```

### 4.3. Nhiệm vụ Diễn tập Vận hành (Operational Drill Tasks)
1. Lên lịch định kỳ hàng quý diễn tập phục hồi từ bản sao lưu sang một instance PostgreSQL độc lập để kiểm chứng tính toàn vẹn dữ liệu (Data Integrity Drill).
2. Tích hợp upload bản sao lưu `.sql.gz` lên lưu trữ ngoài (Offsite Storage: Cloudflare R2 hoặc AWS S3 Glacier).

---

## 5. Quy trình Triển khai & Cập nhật Phiên bản (Rollout Runbook)

### Bước 1: Chuẩn bị biến môi trường
Đảm bảo file `.env` sản xuất đã được cấu hình các giá trị mạnh, không dùng fallback mặc định:
```ini
POSTGRES_USER=uniconnect_prod
POSTGRES_PASSWORD=<strong_random_password>
POSTGRES_DB=uniconnect
JWT_SECRET=<strong_64_char_random_string>
TRUSTED_PROXY_IPS=127.0.0.1,172.16.0.0/12,10.0.0.0/8
APP_ENV=production
APP_DEBUG=false
```

### Bước 2: Khởi động hoặc nâng cấp Stack
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Bước 3: Áp dụng Migrations
```bash
docker compose -f docker-compose.prod.yml exec server alembic upgrade head
```

### Bước 4: Xác thực sau Triển khai (Post-Deployment Smoke Test)
```bash
# 1. Kiểm tra Liveness Nginx
curl -f http://localhost/health

# 2. Kiểm tra Readiness Backend + DB
curl -f http://localhost/api/health

# 3. Kiểm tra SPA Routing
curl -I http://localhost/calendar
```
