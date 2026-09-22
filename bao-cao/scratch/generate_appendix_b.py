import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
from test_diagrams import check_latex_balance

tables = [
    ("users", "models/users.py", "id", "Không", "email UNIQUE, role CHECK (student, staff, admin)"),
    ("user_follows", "models/users.py", "(follower_id, followed_id)", "users(id)", "PRIMARY KEY kép, self-referential"),
    ("activities", "models/activities.py", "id", "users(id), groups(id)", "status CHECK, coordinates Point, times valid"),
    ("activity_cohosts", "models/groups.py", "id", "activities(id), groups(id)", "UNIQUE (activity_id, group_id)"),
    ("activity_cohost_invitations", "models/groups.py", "id", "activities(id), groups(id), users(id)", "status CHECK (pending, accepted, rejected)"),
    ("groups", "models/groups.py", "id", "users(id)", "name UNIQUE, type CHECK (club, faculty, lab)"),
    ("group_members", "models/groups.py", "id", "groups(id), users(id)", "role CHECK (owner, admin, member), UNIQUE"),
    ("group_join_requests", "models/groups.py", "id", "groups(id), users(id)", "status CHECK (pending, approved, rejected)"),
    ("join_requests", "models/participation.py", "id", "activities(id), users(id)", "status CHECK, UNIQUE (activity_id, user_id)"),
    ("comments", "models/interactions.py", "id", "activities(id), users(id)", "FOREIGN KEY ON DELETE CASCADE"),
    ("content_likes", "models/interactions.py", "id", "users(id)", "target_type CHECK, UNIQUE (user_id, target)"),
    ("reports", "models/reports.py", "id", "users(id)", "status CHECK (pending, resolved, dismissed)"),
    ("notifications", "models/notifications.py", "id", "users(id)", "type CHECK, is_read BOOLEAN"),
    ("trophies", "models/trophies.py", "id", "Không", "code UNIQUE, tier CHECK (bronze, silver, gold, diamond)"),
    ("user_trophies", "models/trophies.py", "id", "users(id), trophies(id)", "UNIQUE (user_id, trophy_id), awarded_at"),
    ("user_busy_slots", "models/calendar.py", "id", "users(id)", "recurrence CHECK, start_time < end_time"),
    ("busy_slot_exceptions", "models/calendar.py", "id", "user_busy_slots(id)", "exception_date DATE, ON DELETE CASCADE"),
    ("user_vacation_periods", "models/calendar.py", "id", "users(id)", "start_date <= end_date"),
    ("custom_forms", "models/forms.py", "id", "activities(id)", "is_active BOOLEAN, schema JSON/Relational"),
    ("form_fields", "models/forms.py", "id", "custom_forms(id)", "field_type CHECK, order INT, is_required"),
    ("admin_audit_logs", "models/admin.py", "id", "users(id)", "action VARCHAR, target_entity, timestamp"),
    ("organization_verification_requests", "models/admin.py", "id", "groups(id), users(id)", "status CHECK, verified_at"),
    ("alembic_version", "migrations (Alembic)", "version_num", "Không", "Khóa chính lưu version băm của migration"),
    ("spatial_ref_sys", "PostGIS Extension", "srid", "Không", "Bảng chuẩn quản lý hệ quy chiếu tọa độ EPSG:4326")
]

latex_content = r"""\section*{PHỤ LỤC B: TỪ ĐIỂN DỮ LIỆU VÀ CƠ SỞ DỮ LIỆU CHI TIẾT}
\addcontentsline{toc}{section}{Phụ lục B: Từ điển dữ liệu và Cơ sở dữ liệu chi tiết}

Phụ lục này mô tả toàn bộ cấu trúc cơ sở dữ liệu quan hệ của hệ thống UniConnect. Để đảm bảo tính chính xác học thuật và ngăn ngừa sai lệch tài liệu (documentation drift), dữ liệu dưới đây được tổng hợp trực tiếp từ database schema thực tế của môi trường Production và các tập tin mô hình SQLAlchemy / migration Alembic tương ứng. Hệ thống bao gồm 22 bảng nghiệp vụ domain, 01 bảng quản lý phiên bản di chuyển lược đồ (Alembic Version) và 01 bảng đối tượng quản lý tọa độ chuẩn không gian (PostGIS Spatial Reference System).

\subsection*{B.1 Bảng tổng hợp Lược đồ Cơ sở dữ liệu (Database Schema Master Table)}

\begin{xltabular}{\textwidth}{|l|p{3.2cm}|p{2.0cm}|p{2.8cm}|X|}
\hline
\textbf{Tên bảng (Table)} & \textbf{Nguồn (Source)} & \textbf{Khóa chính (PK)} & \textbf{Khóa ngoại (FK)} & \textbf{Ràng buộc chính (Constraints)} \\ \hline
\endfirsthead
\hline
\textbf{Tên bảng (Table)} & \textbf{Nguồn (Source)} & \textbf{Khóa chính (PK)} & \textbf{Khóa ngoại (FK)} & \textbf{Ràng buộc chính (Constraints)} \\ \hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
"""

for t, src, pk, fk, cons in tables:
    # escape underscores
    t_esc = t.replace('_', r'\_')
    src_esc = src.replace('_', r'\_')
    pk_esc = pk.replace('_', r'\_')
    fk_esc = fk.replace('_', r'\_')
    cons_esc = cons.replace('_', r'\_')
    latex_content += f"\\texttt{{{t_esc}}} & {src_esc} & {pk_esc} & {fk_esc} & {cons_esc} \\\\ \\hline\n"

latex_content += r"""\end{xltabular}

\subsection*{B.2 Chi tiết các bảng nghiệp vụ trọng yếu}

\subsubsection*{1. Bảng \texttt{activities} (Hoạt động ngoại khóa và sự kiện)}
Lưu trữ thông tin chi tiết của tất cả các hoạt động thể thao, học thuật, tình nguyện và phong trào được tổ chức trong khuôn viên:
\begin{itemize}
    \item \texttt{id} (UUID, Primary Key): Định danh duy nhất của hoạt động.
    \item \texttt{owner\_id} (Integer, FK $\rightarrow$ \texttt{users.id}): Sinh viên hoặc Cán bộ khởi tạo hoạt động.
    \item \texttt{group\_id} (Integer, FK $\rightarrow$ \texttt{groups.id}, Nullable): Câu lạc bộ hoặc Đoàn khoa chủ trì tổ chức.
    \item \texttt{title} (VARCHAR(255), NOT NULL): Tiêu đề hoạt động.
    \item \texttt{description} (TEXT): Nội dung mô tả chi tiết, thể lệ tham gia và yêu cầu trang phục/dụng cụ.
    \item \texttt{location} (GEOMETRY(Point, 4326)): Tọa độ địa lý vĩ độ/kinh độ phục vụ lập chỉ mục không gian GIST PostGIS.
    \item \texttt{address} (VARCHAR(500)): Tên phòng, giảng đường hoặc địa điểm văn bản trên khuôn viên.
    \item \texttt{start\_time}, \texttt{end\_time} (TIMESTAMP WITH TIME ZONE): Khung giờ diễn ra sự kiện. Ràng buộc: \texttt{start\_time < end\_time}.
    \item \texttt{registration\_deadline} (TIMESTAMP WITH TIME ZONE): Hạn chót đóng đăng ký tham gia.
    \item \texttt{max\_participants} (Integer, Nullable): Giới hạn số lượng tham dự tối đa (Null: không giới hạn).
    \item \texttt{ctxh\_hours} (Float, DEFAULT 0.0): Số ngày Công tác Xã hội sinh viên được ghi nhận sau khi hoàn thành điểm danh.
    \item \texttt{is\_training\_point} (Boolean, DEFAULT False): Cờ đánh dấu sự kiện có tính Điểm rèn luyện.
    \item \texttt{auto\_approve} (Boolean, DEFAULT True): Cơ chế duyệt tự động hay thủ công cho người tham gia.
    \item \texttt{status} (VARCHAR(50)): Trạng thái vòng đời: \texttt{published}, \texttt{ongoing}, \texttt{completed}, \texttt{cancelled}.
\end{itemize}

\subsubsection*{2. Bảng \texttt{join\_requests} (Đăng ký và Xác thực Điểm danh)}
Lưu trữ quan hệ đăng ký tham gia, đối soát thời gian và bằng chứng điểm danh chống gian lận:
\begin{itemize}
    \item \texttt{id} (Integer, Primary Key): Định danh bản ghi đăng ký.
    \item \texttt{activity\_id} (UUID, FK $\rightarrow$ \texttt{activities.id}): Hoạt động được đăng ký.
    \item \texttt{user\_id} (Integer, FK $\rightarrow$ \texttt{users.id}): Sinh viên tham gia. Ràng buộc: \texttt{UNIQUE(activity\_id, user\_id)}.
    \item \texttt{status} (VARCHAR(50)): Trạng thái: \texttt{pending}, \texttt{approved}, \texttt{rejected}, \texttt{attended}.
    \item \texttt{attendance\_confirmed} (Boolean, DEFAULT False): Cờ đánh dấu xác nhận điểm danh hợp lệ.
    \item \texttt{checkin\_method} (VARCHAR(50), Nullable): Phương thức xác thực: \texttt{qr\_hmac} hoặc \texttt{gps\_radar}.
    \item \texttt{checkin\_time} (TIMESTAMP WITH TIME ZONE, Nullable): Dấu thời gian ghi nhận điểm danh chính xác.
    \item \texttt{checkin\_distance\_meters} (Float, Nullable): Khoảng cách thực tế giữa tọa độ GPS của thiết bị và tâm sự kiện.
    \item \texttt{certificate\_code} (VARCHAR(100), Nullable, UNIQUE): Mã tra cứu chứng nhận trực tuyến định dạng \texttt{UC-\{activity\_id\}-\{user\_id\}}.
\end{itemize}

\subsubsection*{3. Bảng \texttt{activity\_cohosts} \& \texttt{activity\_cohost\_invitations} (Đồng tổ chức và Ủy quyền RBAC)}
Hiện thực liên kết hợp tác giữa các Câu lạc bộ, phục vụ cơ chế phân quyền ủy nhiệm (Delegated RBAC):
\begin{itemize}
    \item \texttt{activity\_id} (UUID, FK $\rightarrow$ \texttt{activities.id}): Sự kiện được ủy quyền quản lý chung.
    \item \texttt{group\_id} (Integer, FK $\rightarrow$ \texttt{groups.id}): Câu lạc bộ được cấp tư cách Đồng tổ chức.
    \item \texttt{status} (VARCHAR(50)): Trạng thái lời mời: \texttt{pending}, \texttt{accepted}, \texttt{declined}.
    \item Quyền hạn kế thừa: Cán bộ thuộc nhóm Đồng tổ chức ở trạng thái \texttt{accepted} có quyền kích hoạt phiên điểm danh (\texttt{can\_open\_checkin = True}) và duyệt sinh viên tham gia.
\end{itemize}

\subsubsection*{4. Bảng \texttt{trophies} \& \texttt{user\_trophies} (Trò chơi hóa - Gamification)}
Quản lý hệ thống thành tích, danh hiệu và tiến trình phấn đấu ngoại khóa của sinh viên:
\begin{itemize}
    \item \texttt{code} (VARCHAR(100), UNIQUE): Mã định danh danh hiệu (ví dụ: \texttt{VOLUNTEER\_PIONEER}, \texttt{SPORTS\_ENTHUSIAST}).
    \item \texttt{tier} (VARCHAR(50)): Cấp bậc danh hiệu: \texttt{BRONZE}, \texttt{SILVER}, \texttt{GOLD}, \texttt{DIAMOND}.
    \item \texttt{criteria\_type} (VARCHAR(50)): Tiêu chí mở khóa: \texttt{ctxh\_milestone}, \texttt{activities\_joined}, \texttt{streak\_days}.
    \item \texttt{threshold\_value} (Float): Ngưỡng giá trị kích hoạt tự động trao thưởng.
\end{itemize}
"""

ok, msg = check_latex_balance(latex_content)
print(f"Appendix B Balance: {ok} ({msg})")

with open('c:/Users/Admin/Code/uniconnect-v2/bao-cao/Sections/Appendix-B-Database.tex', 'w', encoding='utf-8') as f:
    f.write(latex_content)
print("Appendix-B-Database.tex written successfully.")
