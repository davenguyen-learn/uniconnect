import plantuml
from PIL import Image

server = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/img/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}}
)

skin_uml = """skinparam backgroundColor #FFFFFF
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
skinparam activityRoundCorner 8
skinparam conditionStyle diamond
skinparam conditionBackgroundColor #FFF8E1
skinparam conditionBorderColor #FFA000
skinparam conditionFontColor #B78103
skinparam conditionFontSize 11
"""

# Part 1: Client Flow
p1 = f"""@startuml
{skin_uml}
title Quy trình Khởi tạo Hoạt động (Phần 1: Thao tác phía Client)

start
:Chọn tọa độ trên bản đồ;
:Mở biểu mẫu tạo sự kiện;
:Nhập thông tin và cấu hình;
:Nhấn gửi yêu cầu xuất bản;

if (Dữ liệu hợp lệ?) then ([Không])
  :Hiển thị lỗi nhập liệu;
  stop
else ([Hợp lệ])
  :Gửi yêu cầu lên máy chủ;
  :(A) Chuyển tiếp sang Backend;
  stop
endif
@enduml"""

# Part 2: Backend Flow
p2 = f"""@startuml
{skin_uml}
title Quy trình Khởi tạo Hoạt động (Phần 2: Xử lý phía Máy chủ)

start
:(A) Tiếp nhận yêu cầu tạo;
:Xác thực danh tính người dùng;

if (Quyền hạn hợp lệ?) then ([Không])
  :Từ chối và báo lỗi phân quyền;
  stop
else ([Hợp lệ])
  :Lưu thông tin sự kiện;
  
  fork
    :Phản hồi tạo thành công;
    :Cập nhật điểm ghim bản đồ;
    stop
  fork again
    :Tạo vector nhúng ngữ nghĩa;
    :Lưu trữ vector sự kiện;
    stop
  end fork
endif
@enduml"""

d1 = server.processes(p1)
with open("Images/activity-create-activity-part1.png", "wb") as f:
    f.write(d1)

d2 = server.processes(p2)
with open("Images/activity-create-activity-part2.png", "wb") as f:
    f.write(d2)

im1 = Image.open("Images/activity-create-activity-part1.png")
im2 = Image.open("Images/activity-create-activity-part2.png")
print("New Part 1 dimensions:", im1.size)
print("New Part 2 dimensions:", im2.size)
