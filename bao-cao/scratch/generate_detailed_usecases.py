import plantuml

server = plantuml.PlantUML(url='http://www.plantuml.com/plantuml/img/')

# Common skinparam
skin = """skinparam backgroundColor #FFFFFF
skinparam packageStyle rectangle
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 12
skinparam arrowColor #333333
"""

# 1. Tao hoat dong
puml_tao = f"""@startuml
left to right direction
{skin}
actor "Người dùng" as User

rectangle "Hệ thống UniConnect" {{
  usecase "Tạo hoạt động trên bản đồ" as UC
}}

User -- UC
@enduml"""

# 2. Quan ly hoat dong
puml_quanly = f"""@startuml
left to right direction
{skin}
actor "Người dùng" as User

rectangle "Hệ thống UniConnect" {{
  usecase "Quản lý hoạt động" as UC
  
  usecase "Sửa thông tin hoạt động" as UC1
  usecase "Xóa/Hủy hoạt động" as UC2
  usecase "Duyệt thành viên" as UC3
  usecase "Loại bỏ thành viên" as UC4
  usecase "Mời thành viên" as UC5

  UC <.down. UC1 : <<extend>>
  UC <.down. UC2 : <<extend>>
  UC <.down. UC3 : <<extend>>
  UC <.down. UC4 : <<extend>>
  UC <.down. UC5 : <<extend>>
}}

User -- UC
@enduml"""

# 3. Tuong tac hoat dong
puml_tuongtac = f"""@startuml
left to right direction
{skin}
actor "Người dùng" as User

rectangle "Hệ thống UniConnect" {{
  usecase "Tương tác với hoạt động" as UC
  
  usecase "Tham gia tự do" as UC1
  usecase "Gửi yêu cầu tham gia" as UC2
  usecase "Rời khỏi hoạt động" as UC3
  usecase "Bình luận/Thảo luận" as UC4

  UC <.down. UC1 : <<extend>>
  UC <.down. UC2 : <<extend>>
  UC <.down. UC3 : <<extend>>
  UC <.down. UC4 : <<extend>>
}}

User -- UC
@enduml"""

# 4. Hoi dap chatbot
puml_chatbot = f"""@startuml
left to right direction
{skin}
actor "Người dùng" as User
actor "Google Gemini API" as Gemini <<External Service>>

rectangle "Hệ thống UniConnect" {{
  usecase "Hỏi đáp và tra cứu thông minh" as UC
  usecase "Truy xuất ngữ nghĩa học liệu" as UC1
  usecase "Truy xuất dữ liệu hoạt động" as UC2
  usecase "Tổng hợp câu trả lời (LLM)" as UC3
}}

User -- UC

UC ..> UC1 : <<include>>
UC ..> UC2 : <<include>>
UC ..> UC3 : <<include>>

UC3 -- Gemini
@enduml"""

# 5. Quan tri
puml_quantri = f"""@startuml
left to right direction
{skin}
actor "Quản trị viên (Admin)" as Admin

rectangle "Hệ thống UniConnect" {{
  usecase "Quản trị và Kiểm duyệt" as UC
  
  usecase "Cấu hình hệ thống" as UC1
  usecase "Quản lý người dùng" as UC2
  usecase "Xử lý báo cáo vi phạm" as UC3

  UC <.down. UC1 : <<extend>>
  UC <.down. UC2 : <<extend>>
  UC <.down. UC3 : <<extend>>
}}

Admin -- UC
@enduml"""

tasks = [
    ("scratch/use_case_tao_hoat_dong.puml", "Images/use-case-tao-hoat-dong.png", puml_tao),
    ("scratch/use_case_quan_ly_hoat_dong.puml", "Images/use-case-quan-ly-hoat-dong.png", puml_quanly),
    ("scratch/use_case_tuong_tac_hoat_dong.puml", "Images/use-case-tuong-tac-hoat-dong.png", puml_tuongtac),
    ("scratch/use_case_hoi_dap_chatbot.puml", "Images/use-case-hoi-dap-chatbot.png", puml_chatbot),
    ("scratch/use_case_quan_tri.puml", "Images/use-case-quan-tri.png", puml_quantri),
]

for puml_file, img_file, content in tasks:
    with open(puml_file, "w", encoding="utf-8") as f:
        f.write(content)
    data = server.processes(content)
    with open(img_file, "wb") as f:
        f.write(data)
    print(f"Rendered {img_file} successfully ({len(data)} bytes)")
