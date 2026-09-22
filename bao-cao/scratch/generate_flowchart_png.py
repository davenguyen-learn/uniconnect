import plantuml
import os

server = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/img/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}}
)

puml_code = """@startuml
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

start
:Nhận sự kiện ứng viên E_c [s_c, e_c)
và danh sách sự kiện đã có E_i [s_i, e_i);

if (max(s_c, s_i) < min(e_c, e_i)?) then ([Đúng: Giao nhau])
  :<b>Xung đột cứng (Hard Conflict)</b>\\nTrùng lặp thời gian tham gia;
  :Gán cờ cảnh báo hard_conflict;
  stop
else ([Sai: Không giao])
  if (min(e_c, e_i) == max(s_c, s_i)?) then ([Đúng: Liền kề])
    :<b>Xung đột mềm (Soft Conflict)</b>\\nCảnh báo sát giờ di chuyển;
    :Gán cờ cảnh báo soft_conflict;
    stop
  else ([Sai: Δt > 0])
    if (Khoảng đệm Δt < 15 phút?) then ([Đúng])
      :<b>Xung đột mềm (Soft Conflict)</b>\\nCảnh báo sát giờ di chuyển;
      :Gán cờ cảnh báo soft_conflict;
      stop
    else ([Sai: Δt ≥ 15m])
      :<b>Không xung đột (No Conflict)</b>\\nLịch trình hoàn toàn khả thi;
      :Bảo toàn dữ liệu (Non-mutating);
      stop
    endif
  endif
endif
@enduml"""

out_path = 'c:/Users/Admin/Code/uniconnect-v2/bao-cao/Images/flowchart-xung-dot-lich.png'
raw_png = server.processes(puml_code)
with open(out_path, 'wb') as f:
    f.write(raw_png)

print("Saved clean flowchart-xung-dot-lich.png, size:", len(raw_png), "bytes")
