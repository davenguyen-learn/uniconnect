import plantuml
from PIL import Image

server = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/img/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}}
)

act_skin = """skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans, Arial, sans-serif"
skinparam defaultFontSize 11
skinparam arrowColor #263238
skinparam activityBackgroundColor #E8F0FE
skinparam activityBorderColor #1976D2
skinparam conditionBackgroundColor #E8F0FE
skinparam conditionBorderColor #1976D2
skinparam partitionBackgroundColor #FAFAFA
skinparam partitionBorderColor #90CAF9
"""

p1 = f"""@startuml
{act_skin}
title Phần 1: Khởi tạo và Cấu hình tại Giao diện Web Client

start
:Người dùng chọn vị trí trên bản đồ Leaflet\\nhoặc nhấn nút "Tạo hoạt động mới";

partition "Giao diện Web Client (Leaflet UI)" {{
  :Hệ thống trích xuất tọa độ GPS (lat, lng);
  :Hiển thị biểu mẫu khởi tạo sự kiện;
  :Người dùng nhập thông tin cơ bản:
  - Tiêu đề, mô tả, danh mục
  - Thời gian bắt đầu và kết thúc
  - Giới hạn số lượng người tham gia;
  
  :Thiết lập cấu hình vận hành:
  - Chế độ duyệt: Tự do hoặc Cần phê duyệt
  - Phương thức điểm danh: Mã QR HMAC 30s hoặc Radar GPS;
  
  if (Người dùng có vai trò edu_org?) then (Có)
    :Cấu hình số ngày CTXH (social_work_days);
    :Thiết lập danh hiệu vinh danh (Trophy);
  else (Không)
    :Mặc định không cấp ngày CTXH;
  endif
  
  if (Đính kèm biểu mẫu khảo sát?) then (Có)
    :Tạo các câu hỏi cho Custom Form;
  endif

  :Nhấn nút "Xuất bản hoạt động";
  
  if (Dữ liệu biểu mẫu hợp lệ?) then (Không hợp lệ)
    :Báo lỗi trên form (thời gian, thông tin thiếu);
    stop
  else (Hợp lệ)
    :Gửi yêu cầu POST /api/v1/activities;
    :(A) Chuyển tiếp xử lý sang Backend;
    stop
  endif
}}
@enduml"""

p2 = f"""@startuml
{act_skin}
title Phần 2: Xử lý Backend FastAPI và Tác vụ ngầm AI Embedding

start
:(A) Tiếp nhận yêu cầu POST /api/v1/activities;

partition "Xử lý Backend (FastAPI)" {{
  :Xác thực token JWT và kiểm tra quyền RBAC;
  :Chuyển đổi tọa độ thành PostGIS Point (EPSG:4326);
  :Lưu bản ghi sự kiện vào CSDL (bảng activities);
  
  if (Có Form hoặc Trophy đính kèm?) then (Có)
    :Lưu custom_forms, form_fields và trophies;
  endif

  fork
    partition "Phản hồi Client và Bản đồ" {{
      :Trả về mã HTTP 201 Created;
      :Web Client tải lại lớp sự kiện trên bản đồ;
      :Hiển thị điểm ghim (Marker) mới cho cộng đồng;
      stop
    }}
  fork again
    partition "Tác vụ chạy ngầm (Background Task AI)" {{
      :Gửi tiêu đề và mô tả sự kiện sang Google Gemini API;
      :Nhận vector nhúng 768 chiều (text-embedding-004);
      :Cập nhật cột embedding trong PostgreSQL (pgvector);
      stop
    }}
  end fork
}}
@enduml"""

d1 = server.processes(p1)
with open("Images/activity-create-activity-part1.png", "wb") as f:
    f.write(d1)

d2 = server.processes(p2)
with open("Images/activity-create-activity-part2.png", "wb") as f:
    f.write(d2)

im1 = Image.open("Images/activity-create-activity-part1.png")
im2 = Image.open("Images/activity-create-activity-part2.png")
print("Part 1 dimensions:", im1.size, "Aspect ratio:", im1.size[0] / im1.size[1])
print("Part 2 dimensions:", im2.size, "Aspect ratio:", im2.size[0] / im2.size[1])
