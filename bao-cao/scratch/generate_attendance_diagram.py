import plantuml

server = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/img/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}}
)

puml_content = """@startuml
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

if (Phương thức?) then ([Mã QR])
  :BTC tạo mã QR xoay động 30s;
  :Người dùng quét mã QR;
  :Gửi token xác thực lên hệ thống;
else ([GPS Radar])
  :BTC mở phiên điểm danh Radar;
  :Người dùng định vị GPS;
  :Gửi tọa độ lên hệ thống;
endif

if (Hợp lệ sự kiện & Đã đăng ký?) then ([Không])
  :Báo lỗi không hợp lệ hoặc quá hạn;
  stop
else ([Hợp lệ])
  if (Loại xác thực?) then ([Mã QR])
    if (Token HMAC hợp lệ?) then ([Không])
      :Báo lỗi mã sai hoặc hết hạn;
      stop
    else ([Hợp lệ])
    endif
  else ([GPS Radar])
    if (Trong bán kính & sai số GPS đạt?) then ([Không])
      :Báo lỗi ngoài bán kính điểm danh;
      stop
    else ([Đạt])
    endif
  endif

  if (Đã điểm danh trước đó?) then ([Đã có])
    :Báo lỗi đã ghi nhận điểm danh;
    stop
  else ([Chưa])
    :Ghi nhận điểm danh thành công;
    :Cập nhật trạng thái tham gia;
    :Kích hoạt cộng ngày CTXH;
    stop
  endif
endif

@enduml"""

try:
    data = server.processes(puml_content)
    with open("bao-cao/Images/activity-diem-danh-da-che-do.png", "wb") as f:
        f.write(data)
    print(f"Generated bao-cao/Images/activity-diem-danh-da-che-do.png successfully: {len(data)} bytes")
except Exception as e:
    print(f"Error: {e}")
