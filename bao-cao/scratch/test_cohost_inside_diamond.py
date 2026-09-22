import plantuml
from PIL import Image
import re

server = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/img/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}}
)
server_svg = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/svg/',
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
skinparam conditionStyle insideDiamond
skinparam ConditionEndStyle none
skinparam conditionBackgroundColor #FFF8E1
skinparam conditionBorderColor #FFA000
skinparam conditionFontColor #B78103
skinparam conditionFontSize 11
"""

act_cohost = f"""@startuml
{skin_uml}
title Quy trình Điều phối Đồng tổ chức Sự kiện giữa các Nhóm

start
:Nhóm chủ trì tạo sự kiện;
:Chọn thêm nhóm đồng tổ chức;
:Tìm kiếm và chọn nhóm đối tác;
:Gửi lời mời đồng tổ chức;
:Chuyển lời mời đến nhóm đối tác;

if (Nhóm đồng ý?) then ([Từ chối])
  :Cập nhật trạng thái từ chối;
  :Thông báo kết quả cho nhóm chủ trì;
  stop
else ([Đồng ý])
  :Thiết lập liên kết đồng tổ chức;
  :Ủy quyền quản trị sự kiện cho nhóm đối tác;
  :Thông báo xác nhận cho nhóm chủ trì;
  stop
endif
@enduml"""

png_data = server.processes(act_cohost)
with open("Images/activity-cohost-workflow.png", "wb") as f:
    f.write(png_data)

svg_data = server_svg.processes(act_cohost).decode('utf-8')

im = Image.open("Images/activity-cohost-workflow.png")
print("New activity-cohost-workflow.png dimensions:", im.size)

# Verify diamond and text
polygons = re.findall(r'<polygon[^>]*points="([^"]*)"[^>]*fill="([^"]*)"', svg_data)
print("Polygons count:", len(polygons))
for pts, fill in polygons:
    if fill == "#FFF8E1":
        print("Diamond found with fill #FFF8E1, points count:", len(pts.split(',')))

# Check empty diamonds
empty_diamonds = re.findall(r'<polygon[^>]*fill="(?:#FFFFFF|none|transparent)"[^>]*>', svg_data)
print("Empty diamonds count:", len(empty_diamonds))
