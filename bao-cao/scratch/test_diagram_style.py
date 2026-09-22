import plantuml
from PIL import Image

server = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/img/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}}
)

# Test clean UML skin
clean_skin = """skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans, Arial, sans-serif"
skinparam defaultFontSize 12
skinparam arrowColor #263238
skinparam arrowFontColor #37474F
skinparam arrowFontSize 11
skinparam activityBackgroundColor #E8F0FE
skinparam activityBorderColor #1976D2
skinparam activityFontColor #0D47A1
skinparam activityFontSize 12
skinparam conditionBackgroundColor #FFF8E1
skinparam conditionBorderColor #FFA000
skinparam conditionFontColor #E65100
skinparam conditionFontSize 11
skinparam conditionStyle diamond
skinparam ConditionEndStyle none
"""

# Part 1: Clean, concise, no attribute names, pure activity UML
p1_clean = f"""@startuml
{clean_skin}
title Quy trình Khởi tạo Hoạt động (Phần 1: Thao tác phía Client)

start
:Chọn vị trí trên bản đồ;
:Mở biểu mẫu tạo sự kiện;
:Nhập thông tin sự kiện;
:Chọn phương thức điểm danh;

if (Tài khoản tổ chức?) then (Đúng)
  :Gán quyền CTXH và Huy hiệu;
else (Sai)
endif

if (Khảo sát thành viên?) then (Có)
  :Thêm biểu mẫu tùy biến;
else (Không)
endif

:Nhấn xuất bản sự kiện;

if (Thông tin hợp lệ?) then (Sai)
  :Cảnh báo lỗi nhập liệu;
  stop
else (Đúng)
  :Gửi yêu cầu tạo hoạt động;
  :(A) Chuyển sang xử lý hệ thống;
  stop
endif
@enduml"""

# Part 2: Clean, concise, no attribute names
p2_clean = f"""@startuml
{clean_skin}
title Quy trình Khởi tạo Hoạt động (Phần 2: Xử lý phía Máy chủ)

start
:(A) Tiếp nhận yêu cầu tạo;
:Xác thực và phân quyền;
:Chuyển đổi tọa độ bản đồ;
:Lưu dữ liệu sự kiện;

fork
  :Phản hồi tạo thành công;
  :Cập nhật điểm ghim bản đồ;
  stop
fork again
  :Sinh vector nhúng sự kiện;
  :Lưu trữ vector ngữ nghĩa;
  stop
end fork
@enduml"""

d1 = server.processes(p1_clean)
with open("Images/test_p1_clean.png", "wb") as f:
    f.write(d1)

d2 = server.processes(p2_clean)
with open("Images/test_p2_clean.png", "wb") as f:
    f.write(d2)

im1 = Image.open("Images/test_p1_clean.png")
im2 = Image.open("Images/test_p2_clean.png")
print("Clean Part 1 dimensions:", im1.size)
print("Clean Part 2 dimensions:", im2.size)
