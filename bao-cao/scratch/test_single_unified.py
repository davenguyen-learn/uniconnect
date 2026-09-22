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

single_puml = f"""@startuml
{skin_uml}
title Quy trình Khởi tạo và Xuất bản Hoạt động trên Bản đồ

start
:Chọn vị trí trên bản đồ;
:Mở biểu mẫu tạo sự kiện;
:Nhập thông tin sự kiện;
:Cấu hình duyệt và điểm danh;
:Nhấn xuất bản sự kiện;

if (Thông tin hợp lệ?) then ([Không])
  :Hiển thị lỗi nhập liệu;
  stop
else ([Hợp lệ])
  :Gửi yêu cầu lên máy chủ;
  :Xác thực danh tính người dùng;
  
  if (Quyền hạn hợp lệ?) then ([Không])
    :Từ chối và báo lỗi phân quyền;
    stop
  else ([Hợp lệ])
    :Lưu dữ liệu sự kiện;
    
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
endif
@enduml"""

data = server.processes(single_puml)
with open("Images/activity-create-activity.png", "wb") as f:
    f.write(data)

img = Image.open("Images/activity-create-activity.png")
print("Single Unified Diagram Dimensions (w, h):", img.size, "Aspect ratio:", img.size[0] / img.size[1])
