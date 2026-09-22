import plantuml

server = plantuml.PlantUML(
    url='http://www.plantuml.com/plantuml/img/',
    request_opts={'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}}
)

skin = """skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans, Arial, sans-serif"
skinparam defaultFontSize 16
skinparam sequenceMessageFontSize 15
skinparam sequenceParticipantFontSize 16
skinparam sequenceActorFontSize 16
skinparam sequenceGroupFontSize 15
skinparam sequenceGroupHeaderFontSize 15
skinparam roundcorner 6
skinparam arrowColor #263238
skinparam arrowThickness 1.5
skinparam participant {
    BackgroundColor #E8F0FE
    BorderColor #1976D2
    FontColor #0D47A1
    FontStyle bold
}
skinparam actor {
    BackgroundColor #E8F0FE
    BorderColor #1976D2
    FontColor #0D47A1
    FontStyle bold
}
skinparam database {
    BackgroundColor #F1F8E9
    BorderColor #558B2F
    FontColor #33691E
    FontStyle bold
}
skinparam sequence {
    LifeLineBorderColor #1976D2
    LifeLineBackgroundColor #E3F2FD
    GroupHeaderFontColor #0D47A1
    GroupBorderColor #1976D2
    GroupBackgroundColor #F5F9FF
}
"""

# 1. Sequence Diagram: Đăng ký tham gia hoạt động
seq_join = f"""@startuml
{skin}
autonumber
actor "Sinh viên" as User
participant "Giao diện Hoạt động\\n(Web Client)" as Client
participant "Dịch vụ Tham gia\\n(Participation Service)" as Service
database "Cơ sở Dữ liệu\\n(PostgreSQL)" as DB

User -> Client: Yêu cầu đăng ký tham gia sự kiện\\n(kèm thông tin biểu mẫu nếu có)
activate Client

Client -> Service: Chuyển tiếp yêu cầu đăng ký tham gia
activate Service

Service -> DB: Truy vấn giới hạn sức chứa và trạng thái đăng ký
activate DB
DB --> Service: Dữ liệu sức chứa, hạn chót và lịch sử đăng ký
deactivate DB

alt Hết sức chứa hoặc đã quá thời hạn đăng ký
    Service --> Client: Từ chối: Sự kiện đã đủ số lượng hoặc đóng cổng tiếp nhận
    Client --> User: Hiển thị thông báo giải thích lý do không thể đăng ký
else Còn sức chứa hợp lệ
    alt Sự kiện yêu cầu Ban Tổ chức xét duyệt
        Service -> DB: Lưu đơn đăng ký với trạng thái Chờ duyệt
        activate DB
        DB --> Service: Xác nhận lưu trữ thành công
        deactivate DB
        Service -> DB: Tạo thông báo gửi đến Ban Tổ chức sự kiện
        activate DB
        DB --> Service: Xác nhận tạo thông báo thành công
        deactivate DB
        Service --> Client: Phản hồi tiếp nhận đơn (Trạng thái: Chờ xét duyệt)
        Client --> User: Hiển thị trạng thái "Đã gửi yêu cầu, đang chờ phê duyệt"
    else Sự kiện mở tự do (Tự động phê duyệt)
        Service -> DB: Ghi nhận tham gia chính thức & Cập nhật tăng số lượng người tham gia (+1)
        activate DB
        DB --> Service: Xác nhận ghi nhận thành công
        deactivate DB
        Service --> Client: Phản hồi xác nhận thành công (Trạng thái: Đã tham gia)
        Client --> User: Cập nhật giao diện: "Đã đăng ký thành công", mở quyền thảo luận
    end
end
deactivate Service
deactivate Client
@enduml"""

# 2. Sequence Diagram: Hỏi đáp trợ lý AI (ReAct + RAG)
seq_chat = f"""@startuml
{skin}
autonumber
actor "Sinh viên" as User
participant "Giao diện Trợ lý\\n(Chat Assistant UI)" as Client
participant "Dịch vụ Trợ lý AI\\n(ReAct Agent Service)" as Service
database "Kho Dữ liệu Vector\\n(pgvector)" as VectorDB
participant "Mô hình Ngôn ngữ Lớn\\n(Google Gemini API)" as Gemini

User -> Client: Đặt câu hỏi tự nhiên (VD: "Chiều nay có sự kiện thể thao nào không?")
activate Client

Client -> Service: Chuyển tiếp câu hỏi hội thoại kèm ngữ cảnh
activate Service

Service -> Gemini: Phân tích ý định & Xác định công cụ (ReAct Prompt + Tool Specs)
activate Gemini
Gemini --> Service: Kích hoạt công cụ: Tìm kiếm sự kiện theo ngữ nghĩa
deactivate Gemini

Service -> Service: Vector hóa chuỗi truy vấn (Mô hình Embedding)

Service -> VectorDB: Tìm kiếm sự kiện tương đồng ngữ nghĩa nhất (Khoảng cách Cosine)
activate VectorDB
VectorDB --> Service: Danh sách sự kiện phù hợp nhất với ngữ cảnh câu hỏi
deactivate VectorDB

Service -> Gemini: Cung cấp dữ liệu sự kiện thực tế để tổng hợp câu trả lời
activate Gemini
Gemini --> Service: Phản hồi tự nhiên (Giải thích quy chế + Đề xuất sự kiện)
deactivate Gemini

Service --> Client: Trả về câu trả lời hoàn chỉnh kèm thẻ sự kiện đề xuất
deactivate Service

Client --> User: Hiển thị câu trả lời trực quan & nút điều hướng bản đồ
deactivate Client
@enduml"""

# Common skin for activity diagrams
act_skin = """skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans, Arial, sans-serif"
skinparam defaultFontSize 11
skinparam ArrowFontName "Noto Sans, Arial, sans-serif"
skinparam ArrowFontColor #263238
skinparam ArrowFontSize 11
skinparam arrowColor #263238
skinparam conditionStyle insideDiamond
skinparam ConditionEndStyle hline
skinparam activityBackgroundColor #E8F0FE
skinparam activityBorderColor #1976D2
skinparam conditionBackgroundColor #E8F0FE
skinparam conditionBorderColor #1976D2
skinparam partitionBackgroundColor #FAFAFA
skinparam partitionBorderColor #90CAF9
"""

# 0. Activity Diagram: Quy trình đăng ký tham gia hoạt động
act_join = f"""@startuml
{act_skin}

start
:Người dùng chọn hoạt động trên bản đồ;
:Nhấn nút "Tham gia";

if (Hoạt động còn chỗ?) then (Hết chỗ)
  :Hiển thị thông báo\\n"Hoạt động đã đầy";
  stop
else (Còn chỗ)
  if (Thời hạn đăng ký?) then (Quá hạn)
    :Hiển thị thông báo\\n"Đã hết hạn đăng ký";
    stop
  else (Trong hạn)
    :Gửi yêu cầu tham gia (Join Request);
    if (Chế độ xét duyệt?) then (Tự do (Auto-Approve))
      :Hệ thống tự động phê duyệt;
      :Cập nhật trạng thái "Đã tham gia";
    else (Cần duyệt)
      :Gửi thông báo tới Chủ sở hữu;
      :Chờ Chủ sở hữu xem xét;
      if (Kết quả xét duyệt?) then (Đồng ý)
        :Cập nhật trạng thái "Đã tham gia";
      else (Từ chối)
        :Thông báo bị từ chối;
        stop
      endif
    endif
    :Gửi thông báo tham gia thành công;
    :Cập nhật điểm ghim (Marker) nổi bật trên bản đồ;
    stop
  endif
endif
@enduml"""

# 3. Activity Diagram: Hỏi đáp trợ lý AI
act_chat = f"""@startuml
{act_skin}

start
:Người dùng nhập câu hỏi vào Chatbot;
:Hệ thống tiếp nhận văn bản truy vấn;

partition "Xử lý ReAct & RAG (Backend)" {{
  :Chuyển câu hỏi thành Vector nhúng (text-embedding-004);
  :Truy vấn Vector DB (PostgreSQL / pgvector);
  
  if (Tìm thấy dữ liệu liên quan?) then (Có)
    :Trích xuất các bản ghi hoạt động / quy chế phù hợp;
    :Gộp ngữ cảnh (Context) vào Prompt hệ thống;
  else (Không)
    :Sử dụng Prompt gốc hội thoại thông thường;
  endif
}}

partition "Suy luận AI (Google Gemini API)" {{
  :Gửi Prompt đã tối ưu tới Google Gemini API;
  :Mô hình phân tích và sinh câu trả lời tự nhiên;
}}

:Định dạng phản hồi Markdown kèm thông tin sự kiện;
:Hiển thị câu trả lời trực quan lên giao diện Chat UI;
stop
@enduml"""

# 4. Activity Diagram: Quy trình Điều phối Đồng tổ chức (Co-hosting Workflow)
act_cohost = f"""@startuml
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

# 5. Sequence Diagram: Xuất và Xác minh Giấy chứng nhận CTXH
seq_cert = f"""@startuml
{skin}
autonumber
actor "Sinh viên" as User
participant "Giao diện Chứng nhận\\n(Web Client)" as Client
participant "Dịch vụ Chứng nhận\\n(Certificate Service)" as Server
database "Cơ sở Dữ liệu\\n(PostgreSQL)" as DB
actor "Bên Thẩm tra / CTSV\\n(Third-party Verifier)" as Verifier

== Quy trình Xuất Giấy chứng nhận ==
User -> Client: Yêu cầu xuất Giấy chứng nhận CTXH (Hoạt động đã hoàn thành)
activate Client
Client -> Server: Chuyển tiếp yêu cầu kết xuất chứng nhận
activate Server

Server -> DB: Đối soát điều kiện hoàn thành sự kiện & xác nhận điểm danh
activate DB
DB --> Server: Dữ liệu chứng thực hợp lệ (Số ngày CTXH, thời gian điểm danh)
deactivate DB

Server -> Server: Khởi tạo mã định danh duy nhất (UUID)\\n& Tạo mã QR kiểm chứng: https://uniconnect.vn/verify?id=UUID
Server -> Server: Kết xuất file PDF đồ họa A4 Landscape (Chữ ký điện tử + QR Code)

Server --> Client: Trả về tệp tài liệu Giấy chứng nhận số
deactivate Server
Client --> User: Tải tệp Giấy chứng nhận PDF về thiết bị
deactivate Client

== Quy trình Xác thực Trực tuyến qua Mã QR ==
Verifier -> Verifier: Quét mã QR trên Giấy chứng nhận (bản in hoặc bản số)
Verifier -> Server: Yêu cầu thẩm tra tính hợp lệ của chứng nhận theo mã định danh
activate Server

Server -> DB: Truy vấn bản ghi chứng nhận gốc trong hệ thống
activate DB
DB --> Server: Bản ghi gốc hợp lệ từ CSDL
deactivate DB

Server --> Verifier: Hiển thị cổng kiểm chứng công khai "Chứng nhận Hợp lệ"\\n(Tên sinh viên, Số ngày CTXH, Tên hoạt động, Đơn vị tổ chức)
deactivate Server
@enduml"""

# 6. State Machine Diagram: Vòng đời Hoạt động & Đăng ký
state_diagram = """@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans, Arial, sans-serif"
skinparam defaultFontSize 11
skinparam ArrowFontName "Noto Sans, Arial, sans-serif"
skinparam arrowColor #263238
skinparam arrowFontColor #37474F
skinparam arrowFontSize 10
skinparam stateBackgroundColor #F0F4F8
skinparam stateBorderColor #0288D1
skinparam stateFontColor #0D47A1
skinparam stateFontStyle bold

state "VÒNG ĐỜI HOẠT ĐỘNG (ACTIVITY LIFECYCLE)" as ActivityLifecycle {
  [*] --> Draft : Tạo mới
  Draft --> Published : Xuất bản
  Published --> Ongoing : Bắt đầu sự kiện
  Ongoing --> Completed : Kết thúc sự kiện
  
  Published --> Cancelled : Host hủy
  Ongoing --> Cancelled : Hủy đột xuất
  Completed --> [*]
  Cancelled --> [*]
}

state "VÒNG ĐỜI THAM GIA & ĐIỂM DANH (JOIN REQUEST LIFECYCLE)" as ParticipationLifecycle {
  [*] --> Pending : Đăng ký (Cần duyệt)
  [*] --> Approved : Đăng ký (Tự do)
  
  Pending --> Approved : Host duyệt
  Pending --> Rejected : Host từ chối
  
  Approved --> Attended : Điểm danh (QR/GPS)
  Attended --> Awarded : Cộng CTXH & Trophy
  
  Approved --> CancelledByMember : Rời sự kiện
  
  Awarded --> [*]
  Rejected --> [*]
  CancelledByMember --> [*]
}
@enduml"""

# 7. Activity Diagram: Quy trình Tạo mới và Xuất bản hoạt động (Chuẩn UML, cô đọng)
act_create = f"""@startuml
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

# 8. Activity Diagram: Quy trình Xuất và Kiểm chứng Giấy chứng nhận CTXH
act_verify_cert = f"""@startuml
skinparam backgroundColor #FFFFFF
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

title Quy trình Xuất và Kiểm chứng Giấy chứng nhận tham gia hoạt động

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
    :Hiển thị xác thực và thông tin hoạt động\\n(kèm minh chứng CTXH nếu có);
    stop
  endif
endif
@enduml"""

# 9. Activity Diagram: Quy trình Kiểm duyệt nội dung và Xử lý Báo cáo vi phạm
act_moderation = f"""@startuml
{act_skin}

start
:Người dùng phát hiện nội dung vi phạm\\n(Sự kiện sai lệch, bình luận phản cảm, gian lận);
:Chọn "Báo cáo vi phạm" và điền lý do, bằng chứng;

partition "Hệ thống UniConnect (Backend)" {{
  :Ghi nhận bản ghi báo cáo vào bảng reports\\n(target_type, target_id, reporter_id, status='pending');
  :Gửi thông báo đẩy tới Ban Quản trị (Admin);
}}

partition "Quản trị viên (Admin Dashboard)" {{
  :Admin truy cập phân hệ Báo cáo vi phạm;
  :Xem danh sách báo cáo đang chờ xử lý (Pending);
  :Mở chi tiết báo cáo và thẩm tra nội dung bị tố cáo;
  
  if (Nội dung có vi phạm tiêu chuẩn cộng đồng?) then (Không vi phạm)
    :Admin chọn "Bác bỏ báo cáo" (Dismiss);
    :Cập nhật trạng thái reports.status = 'rejected';
    :Giữ nguyên nội dung và đóng báo cáo;
  else (Xác định có vi phạm)
    :Admin chọn hình thức chế tài xử lý;
    if (Mức độ vi phạm?) then (Vi phạm nghiêm trọng)
      :Khóa tài khoản người vi phạm\\n(users.is_active = False);
      :Ẩn toàn bộ hoạt động của tài khoản;
    else (Vi phạm nội dung thông thường)
      :Gỡ bỏ nội dung vi phạm khỏi hệ thống\\n(activities.is_active = False hoặc xóa comment);
    endif
    
    partition "Ghi vết và Lưu trữ" {{
      :Ghi nhận thao tác vào bảng admin_audit_logs\\n(admin_id, action_type, target_id, timestamp);
      :Cập nhật trạng thái reports.status = 'resolved';
      :Gửi thông báo kết quả cho người tố cáo;
      :Gửi email cảnh báo vi phạm tới người bị xử lý;
    }}
  endif
}}

stop
@enduml"""

tasks = [
    ("Images/activity-create-activity.png", act_create),
    ("Images/activity-verify-certificate.png", act_verify_cert),
    ("Images/activity-moderation-report.png", act_moderation),
    ("Images/activity-join-activity.png", act_join),
    ("Images/sequence_join_activity.png", seq_join),
    ("Images/sequence-hoi-dap-chatbot.png", seq_chat),
    ("Images/activity-hoi-chatbot.png", act_chat),
    ("Images/activity-cohost-workflow.png", act_cohost),
    ("Images/sequence-verify-certificate.png", seq_cert),
    ("Images/state-machine-lifecycle.png", state_diagram),
]

if __name__ == '__main__':
    for img_file, puml_content in tasks:
        try:
            data = server.processes(puml_content)
            with open(img_file, "wb") as f:
                f.write(data)
            print(f"Generated {img_file} successfully ({len(data)} bytes)")
        except Exception as e:
            print(f"Error generating {img_file}: {e}")
