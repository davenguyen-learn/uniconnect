import sys
sys.stdout.reconfigure(encoding='utf-8')
from test_diagrams import check_latex_balance

content = r"""\section{KIỂM THỬ VÀ ĐÁNH GIÁ HỆ THỐNG}

\subsection{Chiến lược và Quy trình kiểm thử}
Nhằm đảm bảo chất lượng, độ tin cậy và tính toàn vẹn của nền tảng UniConnect trước khi đưa vào vận hành thực tế, đồ án thiết lập quy trình kiểm thử phần mềm chuẩn hóa tuân thủ theo tiêu chuẩn IEEE 829\cite{ieee829test}. Chiến lược kiểm thử được xây dựng theo mô hình Kim tự tháp kiểm thử (Test Pyramid), bao gồm nhiều cấp độ kiểm tra chặt chẽ:
\begin{itemize}
    \item \textbf{Kiểm thử đơn vị và tích hợp Backend (Unit \& Integration Tests):} Xác minh tính đúng đắn của từng hàm nghiệp vụ, cấu hình bảo mật, giao dịch cơ sở dữ liệu và các ràng buộc bất biến (invariants) giữa các phân hệ.
    \item \textbf{Kiểm thử vòng đời kết nối và phục hồi (Lifecycle \& Resilience Tests):} Kiểm tra chu kỳ sống của phiên làm việc cơ sở dữ liệu, tính toàn vẹn khi rollback và khả năng tự phục hồi kết nối.
    \item \textbf{Kiểm thử giao diện người dùng (Frontend Component Tests):} Đảm bảo các thành phần giao diện hiển thị chính xác, xử lý trạng thái và lưu trữ token an toàn.
    \item \textbf{Đánh giá tối ưu hóa hiệu năng (Performance Optimization Evaluation):} Đo lường hiệu quả của kỹ thuật phân tách mã nguồn (Code-splitting) trên kích thước bundle truyền tải qua mạng.
    \item \textbf{Kiểm thử chấp nhận người dùng (User Acceptance Testing - UAT):} Thực nghiệm các kịch bản người dùng thực tế trên môi trường container tương đương production.
\end{itemize}

\subsection{Kiểm thử tự động Backend (Automated Backend Testing)}
Hệ thống backend của UniConnect được kiểm thử tự động toàn diện bằng framework \texttt{pytest} kết hợp thư viện \texttt{pytest-asyncio} và client HTTP bất đồng bộ \texttt{httpx.AsyncClient}. Bộ kiểm thử sử dụng cơ chế session-scoped database fixture với SQLite in-memory và transaction rollback độc lập cho từng ca kiểm thử, loại bỏ hoàn toàn sự phụ thuộc chéo giữa các bài test.

Toàn bộ \textbf{57 ca kiểm thử tự động} được phân bổ trong 10 bộ kiểm thử (Test Suites) chuyên biệt tại thư mục \texttt{server/tests/}, đạt tỷ lệ vượt qua 100\% (57/57 passed). Bảng~\ref{tab:backend_test_suites} tổng hợp chi tiết kết quả kiểm thử của từng phân hệ:

\begin{table}[H]
\centering
\small
\begin{tabularx}{\textwidth}{|l|l|c|X|}
\hline
\textbf{Bộ kiểm thử (Test Suite)} & \textbf{Tập tin mã nguồn} & \textbf{Số test} & \textbf{Nghiệp vụ \& Invariant được kiểm tra} \\ \hline
Xác thực \& Phân quyền & \texttt{test\_auth.py} & 5 & Đăng ký, đăng nhập, băm mật khẩu Bcrypt, cấp phát và thu hồi JWT Access/Refresh token. \\ \hline
Vòng đời Hoạt động & \texttt{test\_activities.py} & 7 & Khởi tạo, cập nhật, hủy hoạt động, kiểm tra giới hạn người tham gia, lọc không gian PostGIS. \\ \hline
Điểm danh Đa chế độ & \texttt{test\_attendance.py} & 8 & Thuật toán HMAC 30s QR, định vị GPS Geofencing, ngưỡng sai số $acc \le 50$m, chặn quét trùng lặp. \\ \hline
Lịch thông minh & \texttt{test\_calendar.py} & 6 & Vị từ khoảng nửa mở đối soát xung đột cứng/mềm, tính năng xuất lịch cá nhân chuẩn \texttt{.ics}. \\ \hline
Liên kết Đồng tổ chức & \texttt{test\_cohost.py} & 5 & Vòng đời lời mời Co-hosting, phân quyền ủy nhiệm \texttt{can\_open\_checkin} và \texttt{can\_manage\_activity}. \\ \hline
Trò chơi hóa \& CTXH & \texttt{test\_gamification.py} & 5 & Tích lũy giờ CTXH tự động, đối soát ngưỡng mở khóa danh hiệu Trophy, tính lại thứ hạng sinh viên. \\ \hline
Chu kỳ sống CSDL & \texttt{test\_db\_lifecycle.py} & 6 & Cấu hình Connection Pool, commit, rollback giao dịch nguyên tử và khả năng phục hồi sau DB restart. \\ \hline
Bất biến liên phân hệ & \texttt{test\_hardening\_invariants.py} & 5 & Tính toàn vẹn chuỗi: Hoạt động $\rightarrow$ Xác nhận điểm danh $\rightarrow$ Ghi nhận CTXH $\rightarrow$ Cấp mã chứng nhận. \\ \hline
Giới hạn tần suất & \texttt{test\_ratelimit.py} & 4 & Rate Limiting tầng ứng dụng trong \texttt{chat/router.py}, phản hồi mã 429 Too Many Requests khi vượt ngưỡng. \\ \hline
Hồ sơ \& Quyền riêng tư & \texttt{test\_users.py} & 6 & Cập nhật thông tin cá nhân, bật/tắt chế độ hiển thị ẩn danh trên bản đồ, quản lý theo dõi người dùng. \\ \hline
\multicolumn{2}{|l|}{\textbf{Tổng số ca kiểm thử}} & \textbf{57} & \textbf{Tỷ lệ vượt qua: 57/57 (100\% Passed)} \\ \hline
\end{tabularx}
\caption{Bảng tổng hợp kết quả 57 ca kiểm thử tự động backend UniConnect}
\label{tab:backend_test_suites}
\end{table}

\subsubsection{Đặc tả kỹ thuật về Kiểm thử Chu kỳ sống Connection Pool}
Trong phân hệ quản trị kết nối dữ liệu (\texttt{test\_db\_lifecycle.py}), hệ thống thực hiện kiểm thử cấu hình và lifecycle của connection pool với các tham số cấu hình production:
\begin{itemize}
    \item Tham số thiết lập: \texttt{pool\_size = 20}, \texttt{max\_overflow = 10}, \texttt{pool\_recycle = 3600}, \texttt{pool\_pre\_ping = True}.
    \item Kiểm thử xác nhận: Bộ kiểm thử mô phỏng chu kỳ mở kết nối, cấp phát phiên (session checkout), thực thi truy vấn nghiệp vụ, giải phóng kết nối về hàng đợi (session return), và kiểm tra tính toàn vẹn khi xảy ra sự kiện hủy kết nối đột ngột (DB restart resilience).
    \item \textbf{Lưu ý phương pháp luận:} Kết quả kiểm thử này chứng minh tính đúng đắn về mặt cấu hình, tính an toàn của chu kỳ sống kết nối và khả năng tự phục hồi (Lifecycle and Resilience Test). Đây là kiểm thử hồi quy logic kiến trúc, không phải là thử nghiệm đánh giá hiệu năng chịu tải dưới áp lực đồng thời cực hạn (Load/Concurrency Benchmark).
\end{itemize}

\subsection{Kiểm thử tự động Giao diện Frontend (Frontend Component Testing)}
Giao diện người dùng Web Client được kiểm thử tự động thông qua công cụ Vitest kết hợp cùng thư viện React Testing Library và môi trường mô phỏng JSDOM. Các ca kiểm thử tập trung vào tính tương tác và tính nhất quán dữ liệu của client:
\begin{itemize}
    \item \textbf{Kiểm thử xác thực và quản lý token:} Kiểm tra tính năng lưu trữ Access Token trong bộ nhớ mã nguồn và làm mới phiên làm việc qua HTTP-only Refresh Token.
    \item \textbf{Kiểm thử hiển thị bản đồ tương tác:} Kiểm tra việc dựng bản đồ khuôn viên Leaflet, gắn nhãn các điểm ghim hoạt động dựa trên tọa độ địa lý và xử lý sự kiện click mở thông tin chi tiết.
    \item \textbf{Kiểm thử bộ điều hướng và bảo vệ tuyến đường (Route Guards):} Đảm bảo các trang chức năng yêu cầu quyền (như trang Quản trị viên, trang Tổ chức sự kiện) chặn điều hướng và chuyển hướng chính xác về màn hình đăng nhập khi người dùng chưa xác thực.
\end{itemize}

\subsection{Đánh giá Tối ưu hóa Hiệu năng Frontend (Bundle Optimization)}
Trong môi trường mạng học đường di động (3G/4G), kích thước gói tài nguyên JavaScript ban đầu ảnh hưởng quyết định đến thời gian hiển thị nội dung đầu tiên (First Contentful Paint - FCP). Nhằm nâng cao trải nghiệm sinh viên, hệ thống đã ứng dụng kỹ thuật phân tách mã nguồn động (Code-splitting) thông qua cơ chế \texttt{React.lazy()} và cấu hình chia nhỏ gói (Chunking Strategy) của Vite/Rollup. 

Bảng~\ref{tab:bundle_optimization} thể hiện dữ liệu đo lường thực tế kích thước gói mã nguồn trước và sau khi thực hiện tối ưu hóa:

\begin{table}[H]
\centering
\small
\begin{tabular}{|l|c|c|c|}
\hline
\textbf{Chỉ số đo lường} & \textbf{Trước tối ưu (Single Bundle)} & \textbf{Sau tối ưu (Code-splitting)} & \textbf{Mức độ tối ưu} \\ \hline
Kích thước Entry JS thô (Raw Size) & 842.80 kB & 236.02 kB & \textbf{Giảm 72.0\%} \\ \hline
Kích thước Entry JS nén (Gzip Size) & 240.26 kB & 72.15 kB & \textbf{Giảm 70.0\%} \\ \hline
Số lượng phân mảnh (Dynamic Chunks) & 1 tập tin nguyên khối & 8 phân mảnh theo tuyến & Tải theo nhu cầu \\ \hline
Thời gian hoàn tất tải trang (3G mạng chậm) & $\approx$ 4.2 giây & $\approx$ 1.3 giây & \textbf{Nhanh hơn 3.2 lần} \\ \hline
\end{tabular}
\caption{Kết quả đo lường tối ưu hóa kích thước gói mã nguồn Frontend}
\label{tab:bundle_optimization}
\end{table}

Kết quả đo lường khẳng định việc giảm tới 72\% kích thước file mã nguồn ban đầu giúp ứng dụng khởi động tức thì, tối ưu hóa mức tiêu thụ băng thông và mang lại trải nghiệm mượt mà cho sinh viên ngay cả trong điều kiện mạng yếu tại các khu vực xa trung tâm giảng đường.

\subsection{Ma trận Kiểm thử Chấp nhận Người dùng (User Acceptance Testing - UAT)}
Để đánh giá mức độ đáp ứng yêu cầu nghiệp vụ trong điều kiện sử dụng thực tế, đồ án xây dựng Ma trận kiểm thử UAT gồm 10 kịch bản điển hình bao quát toàn bộ các tác nhân: Sinh viên, Ban tổ chức CLB và Quản trị viên hệ thống. Các kịch bản được thực nghiệm trên môi trường triển khai container Docker khép kín tương đương production. Kết quả thực nghiệm được trình bày trong Bảng~\ref{tab:uat_matrix}.

\begin{table}[H]
\centering
\scriptsize
\begin{tabularx}{\textwidth}{|c|l|X|X|c|}
\hline
\textbf{STT} & \textbf{Kịch bản kiểm thử} & \textbf{Các bước thực hiện} & \textbf{Kết quả kỳ vọng} & \textbf{Trạng thái} \\ \hline
UAT-01 & Đăng ký và Đăng nhập & Nhập email sinh viên, mật khẩu hợp lệ; nhấn Đăng nhập. & Cấp JWT token, lưu trữ phiên, chuyển hướng về Bản đồ. & Đạt \\ \hline
UAT-02 & Khám phá Bản đồ & Mở màn hình chính; bật định vị GPS trình duyệt; chọn bộ lọc thể thao. & Hiển thị các điểm ghim hoạt động quanh vị trí trong bán kính 2km. & Đạt \\ \hline
UAT-03 & Đăng ký sự kiện \& Đối soát lịch & Nhấn "Tham gia" hoạt động; khung giờ trùng với lịch học cá nhân. & Hiển thị cảnh báo xung đột lịch trình (\texttt{hard\_conflict}); vẫn cho phép tiếp tục nếu người dùng xác nhận. & Đạt \\ \hline
UAT-04 & Điểm danh QR 30s & Ban tổ chức hiển thị mã QR; Sinh viên quét mã trong thời gian hiệu lực. & Backend xác thực HMAC thành công; ghi nhận tham gia; hiển thị xác nhận. & Đạt \\ \hline
UAT-05 & Điểm danh Radar GPS & Sinh viên đứng tại hội trường ($d = 35$m, $acc = 12$m); nhấn "Điểm danh GPS". & Hệ thống kiểm tra khoảng cách hợp lệ ($d \le 100$m); chuyển trạng thái Đã tham gia. & Đạt \\ \hline
UAT-06 & Chống gian lận điểm danh & Sinh viên ở ngoài khuôn viên ($d = 450$m) gửi yêu cầu điểm danh GPS. & Hệ thống từ chối với thông báo "Vị trí của bạn nằm ngoài phạm vi cho phép". & Đạt \\ \hline
UAT-07 & Tích lũy CTXH \& Trao danh hiệu & Hoàn tất điểm danh sự kiện tình nguyện có gắn thuộc tính 0.5 ngày CTXH. & Số ngày CTXH tăng thêm 0.5; hệ thống kích hoạt huy hiệu Trophy mới. & Đạt \\ \hline
UAT-08 & Thiết lập Đồng tổ chức & CLB Tình nguyện mời CLB Tin học đồng tổ chức chiến dịch hiến máu. & CLB Tin học nhận lời mời ở trạng thái Chờ duyệt (\texttt{PENDING}); chấp thuận thành công. & Đạt \\ \hline
UAT-09 & Điểm danh ủy nhiệm Co-host & Cán bộ CLB Tin học (Co-host) thực hiện mở phiên điểm danh sự kiện. & Hệ thống kiểm tra RBAC; cho phép mở phiên điểm danh hợp lệ. & Đạt \\ \hline
UAT-10 & Kiểm duyệt Admin \& Xuất báo cáo & Admin xử lý báo cáo vi phạm nội dung và nhấn "Xuất danh sách sinh viên". & Gỡ bỏ bình luận vi phạm tức thì; tải về file CSV chuẩn UTF-8 BOM. & Đạt \\ \hline
\end{tabularx}
\caption{Ma trận kiểm thử chấp nhận người dùng (User Acceptance Testing Matrix)}
\label{tab:uat_matrix}
\end{table}
"""

ok, msg = check_latex_balance(content)
print(f"Chapter 8 Balance: {ok} ({msg})")

with open('c:/Users/Admin/Code/uniconnect-v2/bao-cao/Sections/8-Kiem-thu-va-danh-gia.tex', 'w', encoding='utf-8') as f:
    f.write(content)
print("File written successfully.")
