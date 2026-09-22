
import plantuml

server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/svg/')

test_code = """@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam conditionStyle diamond
skinparam ConditionEndStyle none

start
:Bước 1;
if (Hợp lệ?) then (Đúng)
  :Bước 2;
else (Sai)
endif
:Bước 3;
stop
@enduml"""

svg = server.processes(test_code)
with open('Images/test_cond_none.svg', 'wb') as f:
    f.write(svg)
print('Done. Length:', len(svg))
