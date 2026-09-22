import plantuml
from PIL import Image

server = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/img/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0'}}
)

skin_uml = """skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans, Arial, sans-serif"
skinparam defaultFontSize 11
skinparam arrowColor #263238
skinparam arrowFontColor #37474F
skinparam arrowFontSize 11
skinparam activityBackgroundColor #E8F0FE
skinparam activityBorderColor #1976D2
skinparam activityFontColor #0D47A1
skinparam activityFontSize 11
skinparam activityRoundCorner 8
skinparam conditionStyle insideDiamond
skinparam ConditionEndStyle none
skinparam conditionBackgroundColor #FFF8E1
skinparam conditionBorderColor #FFA000
skinparam conditionFontColor #B78103
skinparam conditionFontSize 11
"""

test_puml = f"""@startuml
{skin_uml}
title Quy trình Xuất và Kiểm chứng Giấy chứng nhận CTXH trực tuyến

start
:Sinh viên yêu cầu cấp giấy chứng nhận;

if (Đã điểm danh hợp lệ?) then ([Chưa đạt])
  :Báo lỗi chưa hoàn thành sự kiện;
  stop
else ([Hợp lệ])
  :Sinh mã định danh và QR tra cứu;
  :Kết xuất chứng nhận điện tử (PDF);
  :Sinh viên nhận giấy chứng nhận;
  
  :Bên thẩm định quét mã QR tra cứu;
  
  if (Chứng nhận hợp lệ?) then ([Không])
    :Cảnh báo chứng nhận không hợp lệ;
    stop
  else ([Hợp lệ])
    :Hiển thị xác thực và chi tiết CTXH;
    stop
  endif
endif
@enduml"""

png_data = server.processes(test_puml)
with open("bao-cao/Images/test-cert.png", "wb") as f:
    f.write(png_data)

im = Image.open("bao-cao/Images/test-cert.png")
print("Dimensions:", im.size)
