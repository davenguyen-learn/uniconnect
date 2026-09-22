import plantuml

server = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/img/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}}
)
server_svg = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/svg/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}}
)

attendance_puml = """@startuml
skinparam backgroundColor #FFFFFF
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
skinparam conditionStyle insideDiamond
skinparam ConditionEndStyle none
skinparam conditionBackgroundColor #FFF8E1
skinparam conditionBorderColor #FFA000
skinparam conditionFontColor #B78103
skinparam conditionFontSize 11

title Quy trình Điểm danh chống gian lận đa chế độ (HMAC QR & GPS Geofencing)

start
:Người dùng chọn điểm danh;
:Gửi yêu cầu điểm danh sự kiện;

if (Sự kiện diễn ra & Đã duyệt?) then ([Không])
  :Báo lỗi chưa được duyệt hoặc hết giờ;
  stop
else ([Hợp lệ])
  if (Đã điểm danh trước đó?) then ([Đã có])
    :Báo lỗi đã ghi nhận điểm danh;
    stop
  else ([Chưa])
    if (Phương thức điểm danh?) then ([Mã QR])
      :Người dùng quét mã QR xoay động 30s;
      :Gửi token xác thực lên máy chủ;
      if (Token HMAC hợp lệ?) then ([Không])
        :Báo lỗi mã QR sai hoặc quá hạn;
        stop
      else ([Hợp lệ])
        :Xác nhận điểm danh thành công;
        :Cập nhật trạng thái tham gia;
        :Kích hoạt cộng ngày CTXH;
        stop
      endif
    else ([GPS Radar])
      :Thiết bị xác định tọa độ GPS;
      :Gửi vị trí kiểm tra bán kính;
      if (Tọa độ trong bán kính?) then ([Không])
        :Báo lỗi ngoài phạm vi điểm danh;
        stop
      else ([Hợp lệ])
        :Xác nhận điểm danh thành công;
        :Cập nhật trạng thái tham gia;
        :Kích hoạt cộng ngày CTXH;
        stop
      endif
    endif
  endif
endif
@enduml"""

png_data = server.processes(attendance_puml)
with open("bao-cao/Images/activity-diem-danh-da-che-do.png", "wb") as f:
    f.write(png_data)

svg_data = server_svg.processes(attendance_puml).decode('utf-8')
with open("bao-cao/scratch/attendance_clean.svg", "w", encoding='utf-8') as f:
    f.write(svg_data)

import re
from collections import Counter
polygons = re.findall(r'<polygon[^>]*fill="([^"]*)"', svg_data)
print("Polygons Counter:", Counter(polygons))

empty_diamonds = re.findall(r'<polygon[^>]*fill="(?:#FFFFFF|none|transparent)"[^>]*>', svg_data)
print("Empty diamonds count:", len(empty_diamonds))
