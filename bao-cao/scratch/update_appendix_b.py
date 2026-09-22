# -*- coding: utf-8 -*-
appendix_b_content = r"""\section*{PHỤ LỤC B: TỪ ĐIỂN DỮ LIỆU VÀ CƠ SỞ DỮ LIỆU CHI TIẾT}
\addcontentsline{toc}{section}{Phụ lục B: Từ điển dữ liệu và Cơ sở dữ liệu chi tiết}

Database schema hiện tại gồm 24 bảng được kiểm kê trong môi trường kiểm thử production-equivalent, trong đó bao gồm 22 bảng domain và 2 bảng hệ thống/extension tương ứng (\texttt{alembic\_version}, \texttt{spatial\_ref\_sys}). Để đảm bảo tính chính xác học thuật tuyệt đối và loại bỏ hoàn toàn sai lệch tài liệu (documentation drift), toàn bộ dữ liệu dưới đây được trích xuất và đối soát trực tiếp từ các lớp mô hình ORM (SQLAlchemy Models) và migration Alembic thực tế trong mã nguồn backend hệ thống UniConnect.

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
\texttt{users} & modules/users/models.py & \texttt{id} & Không & \texttt{email} UNIQUE, \texttt{username} UNIQUE, \texttt{role} CHECK (\texttt{student}, \texttt{moderator}, \texttt{admin}, \texttt{edu\_org}) \\ \hline
\texttt{user\_follows} & modules/users/models.py & \texttt{(follower\_id, following\_id)} & \texttt{users(id)} & Khóa chính kép, self-referential, ON DELETE CASCADE \\ \hline
\texttt{activities} & modules/activities/models.py & \texttt{id} & \texttt{users(id)}, \texttt{groups(id)}, \texttt{custom\_forms(id)} & \texttt{ck\_nonneg\_participants}, \texttt{privacy} CHECK, \texttt{check\_in\_code} UNIQUE, PostGIS Point, VECTOR(768) \\ \hline
\texttt{activity\_cohosts} & modules/groups/models.py & \texttt{id} & \texttt{activities(id)}, \texttt{groups(id)} & UNIQUE (\texttt{activity\_id}, \texttt{group\_id}), ON DELETE CASCADE \\ \hline
\texttt{activity\_cohost\_invitations} & modules/groups/models.py & \texttt{id} & \texttt{activities(id)}, \texttt{groups(id)} & \texttt{status} (\texttt{pending}, \texttt{accepted}, \texttt{rejected}), ON DELETE CASCADE \\ \hline
\texttt{groups} & modules/groups/models.py & \texttt{id} & \texttt{users(id)}, \texttt{custom\_forms(id)} & \texttt{name} UNIQUE, \texttt{privacy} CHECK (\texttt{public}, \texttt{private}), ON DELETE CASCADE \\ \hline
\texttt{group\_members} & modules/groups/models.py & \texttt{id} & \texttt{groups(id)}, \texttt{users(id)} & \texttt{role} CHECK (\texttt{admin}, \texttt{member}), UNIQUE (\texttt{group\_id}, \texttt{user\_id}) \\ \hline
\texttt{group\_join\_requests} & modules/groups/models.py & \texttt{id} & \texttt{groups(id)}, \texttt{users(id)} & \texttt{status} (\texttt{pending}, \texttt{approved}, \texttt{rejected}), UNIQUE (\texttt{group\_id}, \texttt{user\_id}) \\ \hline
\texttt{join\_requests} & modules/participation/models.py & \texttt{id} & \texttt{activities(id)}, \texttt{users(id)} & \texttt{status} CHECK (\texttt{pending}, \texttt{approved}, \texttt{declined}, \texttt{cancelled}), UNIQUE (\texttt{activity\_id}, \texttt{user\_id}) \\ \hline
\texttt{comments} & modules/interactions/models.py & \texttt{id} & \texttt{activities(id)}, \texttt{users(id)}, \texttt{comments(id)} & ON DELETE CASCADE, \texttt{parent\_id} self-referential phân cấp \\ \hline
\texttt{content\_likes} & modules/interactions/models.py & \texttt{id} & \texttt{activities(id)}, \texttt{users(id)} & UNIQUE (\texttt{activity\_id}, \texttt{user\_id}), ON DELETE CASCADE \\ \hline
\texttt{reports} & modules/reports/models.py & \texttt{id} & \texttt{users(id)} & \texttt{status} (\texttt{pending}, \texttt{resolved}, \texttt{dismissed}), Polymorphic Target \\ \hline
\texttt{notifications} & modules/notifications/models.py & \texttt{id} & \texttt{users(id)}, \texttt{activities(id)} & \texttt{action\_url}, \texttt{is\_read} BOOLEAN, ON DELETE SET NULL \\ \hline
\texttt{trophies} & modules/trophies/models.py & \texttt{id} & \texttt{activities(id)} & \texttt{name} UNIQUE, \texttt{activity\_id} FK (Nullable), ON DELETE CASCADE \\ \hline
\texttt{user\_trophies} & modules/trophies/models.py & \texttt{id} & \texttt{users(id)}, \texttt{trophies(id)}, \texttt{activities(id)} & UNIQUE (\texttt{user\_id}, \texttt{trophy\_id}), ON DELETE CASCADE \\ \hline
\texttt{user\_busy\_slots} & modules/calendar/models.py & \texttt{id} & \texttt{users(id)} & \texttt{recurrence} (\texttt{once}, \texttt{weekly}), \texttt{day\_of\_week}, ON DELETE CASCADE \\ \hline
\texttt{busy\_slot\_exceptions} & modules/calendar/models.py & \texttt{id} & \texttt{user\_busy\_slots(id)} & \texttt{skip\_date} DATE, ON DELETE CASCADE \\ \hline
\texttt{user\_vacation\_periods} & modules/calendar/models.py & \texttt{id} & \texttt{users(id)} & \texttt{start\_date <= end\_date}, ON DELETE CASCADE \\ \hline
\texttt{custom\_forms} & modules/forms/models.py & \texttt{id} & Không & \texttt{title}, \texttt{description}, tái sử dụng cho Activity và Group \\ \hline
\texttt{form\_fields} & modules/forms/models.py & \texttt{id} & \texttt{custom\_forms(id)} & \texttt{field\_type} CHECK (\texttt{text}, \texttt{textarea}, \texttt{checkbox}, \texttt{number}), \texttt{order} INT \\ \hline
\texttt{organization\_verification\_requests} & modules/admin/models.py & \texttt{id} & \texttt{users(id)} & \texttt{status} CHECK (\texttt{pending}, \texttt{approved}, \texttt{rejected}), \texttt{reviewed\_by} FK \\ \hline
\texttt{admin\_audit\_logs} & modules/admin/models.py & \texttt{id} & \texttt{users(id)} & \texttt{action}, \texttt{target\_type}, \texttt{target\_id}, \texttt{metadata\_json} JSONB \\ \hline
\texttt{alembic\_version} & migrations (Alembic) & \texttt{version\_num} & Không & Quản lý phiên bản băm migration của cơ sở dữ liệu \\ \hline
\texttt{spatial\_ref\_sys} & PostGIS Extension & \texttt{srid} & Không & Bảng chuẩn quản lý hệ quy chiếu tọa độ không gian EPSG:4326 \\ \hline
\end{xltabular}

\subsection*{B.2 Chi tiết các bảng nghiệp vụ trọng yếu}

\subsubsection*{1. Bảng \texttt{activities} (Hoạt động ngoại khóa và sự kiện)}
Lưu trữ thông tin chi tiết của tất cả các hoạt động thể thao, học thuật, tình nguyện và phong trào được tổ chức trong khuôn viên:
\begin{itemize}
    \item \texttt{id} (UUID, Primary Key): Định danh duy nhất của hoạt động.
    \item \texttt{host\_id} (UUID, FK $\rightarrow$ \texttt{users.id}, ON DELETE CASCADE): Người dùng khởi tạo và chủ trì hoạt động.
    \item \texttt{group\_id} (UUID, Nullable, FK $\rightarrow$ \texttt{groups.id}, ON DELETE SET NULL): Nhóm sinh viên chủ trì tổ chức.
    \item \texttt{custom\_form\_id} (UUID, Nullable, FK $\rightarrow$ \texttt{custom\_forms.id}, ON DELETE SET NULL): Biểu mẫu khảo sát tùy biến đính kèm.
    \item \texttt{title} (VARCHAR(150), NOT NULL, Index): Tiêu đề tên sự kiện.
    \item \texttt{description} (TEXT, Nullable): Nội dung mô tả chi tiết, thể lệ tham gia hiển thị công khai.
    \item \texttt{private\_description} (TEXT, Nullable): Hướng dẫn, thông tin nội bộ chỉ hiển thị cho thành viên đã được duyệt tham gia.
    \item \texttt{category} (VARCHAR(50), Nullable, Index): Danh mục phân loại hoạt động (Học thuật, Thể thao, Tình nguyện,...).
    \item \texttt{marker\_location} (PostGIS \texttt{geography(POINT, 4326)}, Nullable): Tọa độ địa lý vĩ độ/kinh độ ghim trên bản đồ số OpenStreetMap.
    \item \texttt{meeting\_location} (VARCHAR(200), Nullable): Địa điểm tập trung trên khuôn viên (giảng đường, sân thể thao, sảnh hội trường).
    \item \texttt{embedding} (\texttt{VECTOR(768)}, Nullable): Vector đặc trưng ngữ nghĩa phục vụ Semantic Search và Trợ lý AI RAG.
    \item \texttt{start\_time}, \texttt{end\_time} (TIMESTAMP WITH TIME ZONE, NOT NULL, Index): Khung thời gian diễn ra sự kiện.
    \item \texttt{max\_participants} (INTEGER, NOT NULL): Số lượng người tham gia tối đa cho phép.
    \item \texttt{current\_participants} (INTEGER, NOT NULL, mặc định: 1): Số lượng người tham gia hiện tại đã được chấp thuận. Ràng buộc: \texttt{ck\_nonneg\_participants}.
    \item \texttt{privacy} (Enum: \texttt{public}, \texttt{private}, NOT NULL, mặc định: \texttt{public}): Chế độ riêng tư công khai hoặc nội bộ.
    \item \texttt{require\_approval} (BOOLEAN, NOT NULL, mặc định: True): Cờ yêu cầu người chủ trì duyệt đơn trước khi tham gia.
    \item \texttt{social\_work\_days} (FLOAT, Nullable): Số ngày Công tác Xã hội (CTXH) sinh viên được ghi nhận sau khi hoàn thành điểm danh.
    \item \texttt{attendance\_mode} (VARCHAR(20), NOT NULL, mặc định: \texttt{manual}): Phương thức điểm danh (\texttt{manual}, \texttt{qr\_code}, \texttt{code\_radar}).
    \item \texttt{check\_in\_code} (VARCHAR(64), Nullable, UNIQUE): Mã bí mật/mã số điểm danh dùng trong phiên check-in trực tiếp.
    \item \texttt{check\_in\_radius} (INTEGER, NOT NULL, mặc định: 300 mét): Bán kính cho phép điểm danh theo định vị GPS.
    \item \texttt{is\_deleted} (BOOLEAN, NOT NULL, mặc định: False), \texttt{deleted\_at}: Cơ chế xóa mềm (Soft-delete).
    \item \texttt{created\_at}, \texttt{updated\_at} (TIMESTAMP WITH TIME ZONE, NOT NULL): Dấu thời gian tạo và cập nhật.
\end{itemize}

\subsubsection*{2. Bảng \texttt{join\_requests} (Đăng ký và Xác thực Điểm danh)}
Lưu trữ quan hệ đăng ký tham gia, đối soát thời gian và bằng chứng điểm danh chống gian lận:
\begin{itemize}
    \item \texttt{id} (UUID, Primary Key): Định danh bản ghi đăng ký tham gia.
    \item \texttt{activity\_id} (UUID, FK $\rightarrow$ \texttt{activities.id}, ON DELETE CASCADE): Hoạt động sinh viên đăng ký.
    \item \texttt{user\_id} (UUID, FK $\rightarrow$ \texttt{users.id}, ON DELETE CASCADE): Sinh viên nộp đơn đăng ký. Ràng buộc: \texttt{UNIQUE(activity\_id, user\_id)}.
    \item \texttt{status} (Enum: \texttt{pending}, \texttt{approved}, \texttt{declined}, \texttt{cancelled}, NOT NULL, mặc định: \texttt{pending}): Trạng thái phê duyệt đơn.
    \item \texttt{message} (TEXT, Nullable): Lời nhắn gửi kèm của sinh viên gửi tới ban tổ chức.
    \item \texttt{responded\_at} (TIMESTAMP WITH TIME ZONE, Nullable): Dấu thời gian ban tổ chức phản hồi phê duyệt hoặc từ chối đơn.
    \item \texttt{form\_responses} (JSONB, Nullable): Dữ liệu câu trả lời của sinh viên cho biểu mẫu đăng ký tùy biến đính kèm.
    \item \texttt{attendance\_confirmed} (BOOLEAN, NOT NULL, mặc định: False): Cờ đánh dấu xác nhận điểm danh hợp lệ của sinh viên.
    \item \texttt{created\_at} (TIMESTAMP WITH TIME ZONE, NOT NULL): Thời điểm nộp đơn đăng ký.
\end{itemize}

\subsubsection*{3. Bảng \texttt{activity\_cohosts} \& \texttt{activity\_cohost\_invitations} (Đồng tổ chức và Ủy quyền RBAC)}
Hiện thực liên kết hợp tác giữa các nhóm sinh viên, phục vụ cơ chế phân quyền ủy nhiệm (Delegated RBAC):
\begin{itemize}
    \item \texttt{activity\_cohosts}: Lưu trữ quan hệ đồng tổ chức chính thức gồm \texttt{id} (UUID, PK), \texttt{activity\_id} (UUID, FK), \texttt{group\_id} (UUID, FK). Ràng buộc duy nhất: \texttt{UNIQUE(activity\_id, group\_id)}.
    \item \texttt{activity\_cohost\_invitations}: Quản lý quy trình gửi lời mời gồm \texttt{activity\_id}, nhóm chủ trì \texttt{host\_group\_id} (UUID, FK), nhóm đối tác \texttt{invited\_group\_id} (UUID, FK), trạng thái phản hồi \texttt{status} (VARCHAR(20): \texttt{pending}, \texttt{accepted}, \texttt{rejected}) và lời nhắn kèm \texttt{message} (TEXT).
    \item Quyền hạn kế thừa: Thành viên có quyền quản trị thuộc nhóm Đồng tổ chức ở trạng thái \texttt{accepted} được cấp thẩm quyền mở phiên điểm danh và duyệt đơn sinh viên tham gia sự kiện.
\end{itemize}

\subsubsection*{4. Bảng \texttt{trophies} \& \texttt{user\_trophies} (Trò chơi hóa - Gamification)}
Quản lý hệ thống thành tích, danh hiệu và tiến trình phấn đấu ngoại khóa của sinh viên:
\begin{itemize}
    \item \texttt{trophies}: Danh hiệu vinh danh gồm \texttt{id} (UUID, PK), sự kiện trao thưởng \texttt{activity\_id} (UUID, Nullable, FK $\rightarrow$ \texttt{activities.id}, ON DELETE CASCADE), tên danh hiệu \texttt{name} (VARCHAR(100), UNIQUE) và nội dung giải thích ý nghĩa \texttt{description} (TEXT).
    \item \texttt{user\_trophies}: Bảng ghi nhận danh hiệu trao cho sinh viên gồm \texttt{id} (UUID, PK), người nhận \texttt{user\_id} (UUID, FK $\rightarrow$ \texttt{users.id}, ON DELETE CASCADE), danh hiệu \texttt{trophy\_id} (UUID, FK $\rightarrow$ \texttt{trophies.id}, ON DELETE CASCADE), sự kiện đạt được \texttt{activity\_id} (UUID, Nullable, FK), cùng thời điểm trao tặng \texttt{created\_at}. Ràng buộc: \texttt{UNIQUE(user\_id, trophy\_id)}.
\end{itemize}
"""

with open(r'c:\Users\Admin\Code\uniconnect-v2\bao-cao\Sections\Appendix-B-Database.tex', 'w', encoding='utf-8') as f:
    f.write(appendix_b_content)
print("Appendix B updated successfully!")
