import sys
sys.stdout.reconfigure(encoding='utf-8')
from test_diagrams import check_latex_balance

# Appendix A: Use Cases
appendix_a = r"""\section*{PHỤ LỤC A: DANH MỤC USE CASE VÀ ĐẶC TẢ CHI TIẾT}
\addcontentsline{toc}{section}{Phụ lục A: Danh mục Use Case và Đặc tả chi tiết}

Phụ lục này tổng hợp toàn bộ các ca sử dụng (Use Cases) của hệ thống UniConnect, được phân loại theo từng nhóm tác nhân chính: Sinh viên (Student), Ban tổ chức CLB / Cán bộ trường (Staff/Organizer), Quản trị viên hệ thống (Administrator) và Tác nhân Hệ thống tự động (System Engine).

\subsection*{A.1 Bảng tổng hợp Danh mục Ca sử dụng (Use Case Inventory)}

\begin{xltabular}{\textwidth}{|l|p{4.2cm}|l|X|c|}
\hline
\textbf{Mã UC} & \textbf{Tên ca sử dụng} & \textbf{Tác nhân} & \textbf{Mô tả tóm tắt} & \textbf{Độ ưu tiên} \\ \hline
\endfirsthead
\hline
\textbf{Mã UC} & \textbf{Tên ca sử dụng} & \textbf{Tác nhân} & \textbf{Mô tả tóm tắt} & \textbf{Độ ưu tiên} \\ \hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
UC-AUTH-01 & Đăng ký tài khoản sinh viên & Sinh viên & Tạo tài khoản mới bằng email trường học. & Cao \\ \hline
UC-AUTH-02 & Đăng nhập và Cấp phát JWT & Người dùng & Xác thực mật khẩu Bcrypt, cấp Access/Refresh token. & Cao \\ \hline
UC-AUTH-03 & Đăng nhập Google OAuth2 & Người dùng & Xác thực liên kết tài khoản Google học đường. & Trung bình \\ \hline
UC-MAP-01 & Khám phá hoạt động trên Bản đồ & Sinh viên & Xem các điểm ghim sự kiện lân cận qua PostGIS. & Cao \\ \hline
UC-MAP-02 & Lọc sự kiện theo danh mục & Sinh viên & Lọc hoạt động theo Thể thao, Học thuật, CTXH. & Cao \\ \hline
UC-ACT-01 & Khởi tạo sự kiện / hoạt động & Sinh viên / BTC & Tạo hoạt động ghim tọa độ, thời gian, giới hạn chỗ. & Cao \\ \hline
UC-ACT-02 & Đăng ký tham gia hoạt động & Sinh viên & Gửi yêu cầu tham gia, kiểm tra slot trống. & Cao \\ \hline
UC-ACT-03 & Hủy đăng ký hoạt động & Sinh viên & Rút tên khỏi danh sách tham gia trước hạn chót. & Trung bình \\ \hline
UC-CAL-01 & Đối soát xung đột lịch trình & Hệ thống & Áp dụng vị từ khoảng thời gian giao nhau cảnh báo trùng lặp. & Cao \\ \hline
UC-CAL-02 & Xuất lịch cá nhân chuẩn \texttt{.ics} & Sinh viên & Tải file iCalendar đồng bộ vào Google Calendar. & Trung bình \\ \hline
UC-ATT-01 & Tạo mã QR xoay động 30s HMAC & Ban tổ chức & Sinh mã QR bảo mật tự làm mới mỗi chu kỳ 30 giây. & Cao \\ \hline
UC-ATT-02 & Điểm danh qua quét mã QR & Sinh viên & Quét mã QR xoay động, gửi token lên máy chủ. & Cao \\ \hline
UC-ATT-03 & Điểm danh Radar GPS 1-Chạm & Sinh viên & Gửi tọa độ GPS, kiểm tra bán kính $d \le 100$m. & Cao \\ \hline
UC-ATT-04 & Tra cứu chứng nhận trực tuyến & Công chúng & Kiểm tra mã chứng nhận tại \texttt{/verify-certificate}. & Trung bình \\ \hline
UC-COH-01 & Mời Câu lạc bộ Đồng tổ chức & BTC chính & Gửi lời mời Co-hosting cho CLB đối tác. & Cao \\ \hline
UC-COH-02 & Phê chuẩn lời mời Đồng tổ chức & CLB đối tác & Chấp thuận hoặc từ chối tư cách Đồng tổ chức. & Cao \\ \hline
UC-COH-03 & Điểm danh ủy nhiệm Co-host & CLB đối tác & Cán bộ CLB đối tác mở phiên điểm danh sự kiện. & Cao \\ \hline
UC-GAM-01 & Tự động tích lũy ngày CTXH & Hệ thống & Cộng dồn số ngày CTXH sau khi xác nhận điểm danh. & Cao \\ \hline
UC-GAM-02 & Mở khóa huy hiệu danh dự & Hệ thống & Trao Trophy khi sinh viên đạt mốc thành tích. & Trung bình \\ \hline
UC-RAG-01 & Tư vấn quy chế và hoạt động & Sinh viên & Đặt câu hỏi cho Trợ lý AI qua kiến trúc RAG. & Cao \\ \hline
UC-ADM-01 & Quản trị người dùng và vai trò & Quản trị viên & Khóa tài khoản, nâng cấp vai trò Cán bộ/Admin. & Cao \\ \hline
UC-ADM-02 & Kiểm duyệt nội dung vi phạm & Quản trị viên & Xử lý báo cáo, gỡ bỏ bình luận/sự kiện vi phạm. & Cao \\ \hline
UC-ADM-03 & Xuất danh sách sinh viên CSV & Quản trị viên & Trích xuất dữ liệu rèn luyện chuẩn UTF-8 BOM. & Cao \\ \hline
\end{xltabular}
"""

# Appendix C: API Endpoints
appendix_c = r"""\section*{PHỤ LỤC C: DANH MỤC API ENDPOINTS HỆ THỐNG}
\addcontentsline{toc}{section}{Phụ lục C: Danh mục API Endpoints hệ thống}

Phụ lục này tài liệu hóa chi tiết các giao diện lập trình ứng dụng (RESTful API) được hiện thực trong phân hệ backend FastAPI của UniConnect. Tất cả các endpoint đều tuân thủ kiến trúc RESTful, dữ liệu trao đổi định dạng JSON chuẩn UTF-8, và được bảo vệ thông qua cơ chế xác thực JWT Bearer Token tại tầng phụ thuộc (Dependency Injection).

\subsection*{C.1 Bảng tổng hợp Giao diện API theo Phân hệ}

\begin{xltabular}{\textwidth}{|l|l|c|X|}
\hline
\textbf{Phương thức} & \textbf{Đường dẫn (Endpoint Path)} & \textbf{Xác thực} & \textbf{Mô tả nghiệp vụ} \\ \hline
\endfirsthead
\hline
\textbf{Phương thức} & \textbf{Đường dẫn (Endpoint Path)} & \textbf{Xác thực} & \textbf{Mô tả nghiệp vụ} \\ \hline
\endhead
\hline
\endfoot
\hline
\endlastfoot

\multicolumn{4}{|l|}{\textbf{1. Phân hệ Xác thực \& Tài khoản (Auth \& Users)}} \\ \hline
\texttt{POST} & \texttt{/api/v1/auth/register} & Không & Đăng ký tài khoản sinh viên mới bằng email trường học. \\ \hline
\texttt{POST} & \texttt{/api/v1/auth/login} & Không & Đăng nhập, xác thực mật khẩu Bcrypt, trả về JWT Token. \\ \hline
\texttt{GET} & \texttt{/api/v1/users/me} & Bearer & Lấy thông tin hồ sơ cá nhân và quyền hạn người dùng hiện tại. \\ \hline
\texttt{PATCH} & \texttt{/api/v1/users/me} & Bearer & Cập nhật thông tin tiểu sử, avatar và tùy chọn quyền riêng tư. \\ \hline
\texttt{GET} & \texttt{/api/v1/users/\{id\}/stats} & Bearer & Xem thống kê hoạt động, số giờ CTXH và thứ hạng sinh viên. \\ \hline
\texttt{POST} & \texttt{/api/v1/users/\{id\}/follow} & Bearer & Bắt đầu theo dõi hoạt động của sinh viên hoặc Câu lạc bộ khác. \\ \hline

\multicolumn{4}{|l|}{\textbf{2. Phân hệ Hoạt động \& Bản đồ (Activities \& Map)}} \\ \hline
\texttt{GET} & \texttt{/api/v1/activities/nearby} & Tùy chọn & Truy vấn không gian PostGIS lọc sự kiện theo tọa độ bán kính. \\ \hline
\texttt{POST} & \texttt{/api/v1/activities} & Bearer & Khởi tạo sự kiện mới kèm tọa độ, khung giờ và cấu hình CTXH. \\ \hline
\texttt{GET} & \texttt{/api/v1/activities/\{id\}} & Tùy chọn & Lấy thông tin chi tiết sự kiện, số lượng đăng ký và danh sách Co-host. \\ \hline
\texttt{PATCH} & \texttt{/api/v1/activities/\{id\}} & Bearer & Chỉnh sửa thông tin sự kiện (chỉ dành cho Chủ trì hoặc Co-host). \\ \hline
\texttt{DELETE} & \texttt{/api/v1/activities/\{id\}} & Bearer & Hủy sự kiện và tự động gửi thông báo đến người đã đăng ký. \\ \hline

\multicolumn{4}{|l|}{\textbf{3. Phân hệ Tham gia \& Điểm danh (Participation \& Attendance)}} \\ \hline
\texttt{POST} & \texttt{/api/v1/activities/\{id\}/join} & Bearer & Đăng ký tham gia sự kiện; kiểm tra slot và xung đột lịch trình. \\ \hline
\texttt{GET} & \texttt{/api/v1/activities/\{id\}/check-in-code} & Bearer & Tạo mã QR xoay động 30s HMAC-SHA256 (dành cho BTC). \\ \hline
\texttt{POST} & \texttt{/api/v1/activities/\{id\}/check-in} & Bearer & Điểm danh sinh viên: đối soát mã QR HMAC hoặc tọa độ GPS. \\ \hline
\texttt{GET} & \texttt{/api/v1/activities/\{id\}/participants} & Bearer & Danh sách sinh viên tham dự kèm trạng thái điểm danh thực tế. \\ \hline
\texttt{GET} & \texttt{/api/v1/certificates/verify/\{code\}} & Không & Cổng công khai đối soát tính nguyên bản của Giấy chứng nhận CTXH. \\ \hline

\multicolumn{4}{|l|}{\textbf{4. Phân hệ Lịch thông minh (Smart Calendar)}} \\ \hline
\texttt{GET} & \texttt{/api/v1/calendar/events} & Bearer & Lấy danh sách sự kiện đã đăng ký trong tháng của sinh viên. \\ \hline
\texttt{POST} & \texttt{/api/v1/calendar/check-conflict} & Bearer & Kiểm tra xung đột thời gian dựa trên vị từ giao nhau thời gian. \\ \hline
\texttt{GET} & \texttt{/api/v1/calendar/busy-slots} & Bearer & Quản lý danh sách khung giờ bận cá nhân lặp lại hàng tuần. \\ \hline
\texttt{POST} & \texttt{/api/v1/calendar/busy-slots} & Bearer & Thêm mới lịch bận cố định (lịch học, lịch làm thêm cá nhân). \\ \hline

\multicolumn{4}{|l|}{\textbf{5. Phân hệ Câu lạc bộ \& Đồng tổ chức (Groups \& Co-hosting)}} \\ \hline
\texttt{GET} & \texttt{/api/v1/groups/discover} & Tùy chọn & Danh sách các Câu lạc bộ, Đội, Nhóm và Đoàn khoa trong trường. \\ \hline
\texttt{POST} & \texttt{/api/v1/activities/\{id\}/invite-cohost} & Bearer & Mời Câu lạc bộ khác làm Đồng tổ chức sự kiện (Primary Owner). \\ \hline
\texttt{POST} & \texttt{/api/v1/groups/co-host-invitations/\{id\}/respond} & Bearer & Phê chuẩn hoặc từ chối tham gia Đồng tổ chức sự kiện. \\ \hline
\texttt{GET} & \texttt{/api/v1/groups/\{id\}/members} & Bearer & Danh sách thành viên và phân quyền vai trò trong nội bộ CLB. \\ \hline

\multicolumn{4}{|l|}{\textbf{6. Phân hệ Trò chơi hóa \& Trợ lý AI (Gamification \& AI)}} \\ \hline
\texttt{GET} & \texttt{/api/v1/trophies/user/\{id\}} & Bearer & Danh sách danh hiệu Trophy đã đạt và tiến trình phấn đấu tiếp theo. \\ \hline
\texttt{POST} & \texttt{/api/v1/chat/ask} & Bearer & Gửi câu hỏi cho Trợ lý AI theo kiến trúc RAG (Rate Limiting). \\ \hline

\multicolumn{4}{|l|}{\textbf{7. Phân hệ Quản trị hệ thống (Admin Dashboard)}} \\ \hline
\texttt{GET} & \texttt{/api/v1/admin/metrics} & Admin & Lấy số liệu KPI tăng trưởng người dùng, sự kiện và lượt điểm danh. \\ \hline
\texttt{GET} & \texttt{/api/v1/admin/reports} & Admin & Danh sách báo cáo vi phạm nội dung đang chờ ban điều hành xử lý. \\ \hline
\texttt{POST} & \texttt{/api/v1/admin/reports/\{id\}/review} & Admin & Xử lý báo cáo: gỡ bỏ nội dung vi phạm hoặc bác bỏ tố cáo. \\ \hline
\texttt{GET} & \texttt{/api/v1/admin/students/export} & Admin & Xuất toàn bộ dữ liệu sinh viên và ngày CTXH dạng CSV UTF-8 BOM. \\ \hline
\end{xltabular}
"""

ok_a, msg_a = check_latex_balance(appendix_a)
print(f"Appendix A Balance: {ok_a} ({msg_a})")

ok_c, msg_c = check_latex_balance(appendix_c)
print(f"Appendix C Balance: {ok_c} ({msg_c})")

with open('c:/Users/Admin/Code/uniconnect-v2/bao-cao/Sections/Appendix-A-UseCases.tex', 'w', encoding='utf-8') as f:
    f.write(appendix_a)

with open('c:/Users/Admin/Code/uniconnect-v2/bao-cao/Sections/Appendix-C-API.tex', 'w', encoding='utf-8') as f:
    f.write(appendix_c)

print("Appendix A and C written successfully.")
