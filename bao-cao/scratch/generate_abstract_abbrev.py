import sys
sys.stdout.reconfigure(encoding='utf-8')
from test_diagrams import check_latex_balance

# 1. Update 0.4-Tom-tat-de-tai.tex
vn_abstract = r"""\begin{center}
    \Large{\textbf{TÓM TẮT ĐỀ TÀI}}
\end{center}

Trong môi trường giáo dục đại học hiện đại, việc thiếu hụt các nền tảng số hỗ trợ tương tác dựa trên vị trí thực tế và tích hợp quản lý phong trào đang tạo ra rào cản lớn đối với sinh viên trong việc khám phá hoạt động ngoại khóa, ghi nhận ngày công tác xã hội và xây dựng mạng lưới học thuật. Nhằm giải quyết triệt để vấn đề này, đề tài tiến hành nghiên cứu, thiết kế và phát triển nền tảng \textbf{UniConnect}---hệ thống kết nối và quản lý hoạt động học đường thông minh dành cho các trường đại học.

Hệ thống được kiến trúc xoay quanh 5 trụ cột nghiệp vụ then chốt: (1) \textbf{Bản đồ tương tác không gian:} Ứng dụng PostGIS lập chỉ mục không gian hỗ trợ định vị và khám phá sự kiện quanh khuôn viên trường theo thời gian thực; (2) \textbf{Hệ thống điểm danh chống gian lận đa chế độ:} Kết hợp mã QR xoay động 30 giây thuật toán HMAC-SHA256 với định vị Geofencing GPS, tuân thủ nguyên tắc thiết kế xem dữ liệu thiết bị client là đầu vào chưa tin cậy và backend là nguồn chân lý duy nhất; (3) \textbf{Lịch thông minh quản lý xung đột:} Áp dụng thuật toán vị từ khoảng thời gian giao nhau đối soát xung đột lịch trình tự động và xuất file chuẩn iCalendar \texttt{.ics}; (4) \textbf{Cơ chế Đồng tổ chức (Co-hosting RBAC) \& Trò chơi hóa:} Phân quyền ủy nhiệm giữa các Câu lạc bộ, tự động hóa quy trình ghi nhận ngày Công tác Xã hội (CTXH) và mở khóa danh hiệu Trophy; (5) \textbf{Trợ lý học đường AI:} Tích hợp kiến trúc RAG hỗ trợ giải đáp quy chế và gợi ý hoạt động cá nhân hóa.

Hệ thống được triển khai trên hạ tầng container Docker production khép kín gồm Nginx reverse proxy, FastAPI (Python 3.11) vận hành dưới người dùng non-root với cơ chế Rate Limiting tầng ứng dụng, và PostgreSQL tích hợp PostGIS/pgvector. Toàn bộ 57 bài kiểm thử tự động backend và 3 bài kiểm thử frontend đều vượt qua 100\%, đồng thời kỹ thuật chia nhỏ gói (Code-splitting) giúp giảm 72\% dung lượng tải ban đầu. Đồ án khẳng định một giải pháp kỹ thuật phần mềm hoàn chỉnh, bảo mật và sẵn sàng triển khai thực tế.

\textbf{Từ khóa:} Nền tảng học đường, Bản đồ không gian, Điểm danh HMAC, Geofencing, Vị từ khoảng giao nhau, RBAC, Trò chơi hóa, RAG, Docker.

\newpage
\begin{center}
    \Large{\textbf{ABSTRACT}}
\end{center}

In modern higher education environments, the absence of location-aware digital platforms for activity coordination significantly impedes students from discovering campus events, accumulating community service credits, and cultivating meaningful academic networks. To address these challenges, this thesis presents the design, implementation, and empirical evaluation of \textbf{UniConnect}---an integrated campus activity coordination and student engagement platform tailored for university environments.

The platform is structured upon five core technical pillars: (1) \textbf{Spatial Campus Mapping:} Utilizing PostGIS spatial indexing for real-time geofenced activity exploration across campus facilities; (2) \textbf{Multi-mode Anti-fraud Attendance Verification:} Integrating 30-second rotating HMAC-SHA256 QR codes with client GPS geofencing under an authoritative architecture where client inputs are treated as untrusted and the backend serves as the sole source of truth; (3) \textbf{Conflict-aware Smart Calendar Management:} Employing an interval overlap predicate for automated schedule conflict detection and RFC 5545 iCalendar (\texttt{.ics}) export; (4) \textbf{Inter-club Co-hosting RBAC \& Gamification:} Implementing delegated role-based access control for club collaborations and automating Social Work (CTXH) credit accumulation and Trophy progression; (5) \textbf{RAG-based Campus Assistant:} Combining Retrieval-Augmented Generation to answer academic regulations and provide personalized event recommendations.

UniConnect is deployed on a production-grade multi-container topology comprising an Nginx reverse proxy, FastAPI running under least-privilege non-root execution with application-layer rate limiting, and PostgreSQL with PostGIS and pgvector extensions. The entire test suite of 57 automated backend tests and 3 frontend tests achieves a 100\% pass rate, while frontend code-splitting delivers a 72\% reduction in initial bundle size (from 842.8 kB to 236.0 kB). The thesis demonstrates a robust, verified, and production-ready software engineering solution for smart university campuses.

\textbf{Keywords:} Campus Social Platform, Geofencing, HMAC-SHA256, Interval Predicate, Co-hosting RBAC, Gamification, Retrieval-Augmented Generation, Production Docker.
"""

# Check and write 0.4
ok1, msg1 = check_latex_balance(vn_abstract)
print(f"Abstract Balance: {ok1} ({msg1})")
with open('c:/Users/Admin/Code/uniconnect-v2/bao-cao/Sections/0.4-Tom-tat-de-tai.tex', 'w', encoding='utf-8') as f:
    f.write(vn_abstract)

# 2. Create 0.8-Danh-muc-tu-viet-tat.tex
abbreviations = r"""\begin{center}
    \Large{\textbf{DANH MỤC TỪ VIẾT TẮT}}
\end{center}
\addcontentsline{toc}{section}{Danh mục từ viết tắt}

\vspace{0.5cm}

\begin{xltabular}{\textwidth}{|l|l|X|}
\hline
\textbf{Từ viết tắt} & \textbf{Thuật ngữ tiếng Anh} & \textbf{Ý nghĩa tiếng Việt} \\ \hline
\endfirsthead
\hline
\textbf{Từ viết tắt} & \textbf{Thuật ngữ tiếng Anh} & \textbf{Ý nghĩa tiếng Việt} \\ \hline
\endhead
\hline
\endfoot
\hline
\endlastfoot
API & Application Programming Interface & Giao diện lập trình ứng dụng \\ \hline
BOM & Byte Order Mark & Ký tự đánh dấu thứ tự byte trong file UTF-8 \\ \hline
Bcrypt & Blowfish Crypt & Thuật toán băm mật khẩu bảo mật \\ \hline
CSP & Content Security Policy & Chính sách bảo mật nội dung trình duyệt \\ \hline
CSV & Comma-Separated Values & Định dạng tập tin dữ liệu phân tách bởi dấu phẩy \\ \hline
CTXH & Social Work / Community Service & Công tác Xã hội \\ \hline
ERD & Entity-Relationship Diagram & Sơ đồ quan hệ thực thể \\ \hline
FCP & First Contentful Paint & Thời gian hiển thị phần tử nội dung đầu tiên \\ \hline
GIS & Geographic Information System & Hệ thống thông tin địa lý \\ \hline
GPS & Global Positioning System & Hệ thống định vị toàn cầu \\ \hline
HMAC & Hash-based Message Authentication Code & Mã xác thực thông điệp dựa trên hàm băm \\ \hline
HTTPS & Hypertext Transfer Protocol Secure & Giao thức truyền tải siêu văn bản an toàn \\ \hline
JWT & JSON Web Token & Chuỗi mã hóa tiêu chuẩn mở trao đổi thông tin bảo mật \\ \hline
LLM & Large Language Model & Mô hình ngôn ngữ lớn \\ \hline
ORM & Object-Relational Mapping & Kỹ thuật ánh xạ đối tượng vào cơ sở dữ liệu quan hệ \\ \hline
PostGIS & PostgreSQL Geographic Information System & Tiện ích mở rộng xử lý không gian trên PostgreSQL \\ \hline
RAG & Retrieval-Augmented Generation & Kỹ thuật sinh nội dung tăng cường bằng truy xuất tri thức \\ \hline
RBAC & Role-Based Access Control & Mô hình kiểm soát truy cập dựa trên vai trò \\ \hline
REST & Representational State Transfer & Phong cách kiến trúc hướng dịch vụ tiêu chuẩn Web \\ \hline
RFC & Request for Comments & Tài liệu tiêu chuẩn kỹ thuật Internet \\ \hline
SPA & Single Page Application & Ứng dụng web đơn trang \\ \hline
TLS & Transport Layer Security & Giao thức bảo mật tầng truyền tải \\ \hline
TOTP & Time-based One-Time Password & Mật khẩu dùng một lần dựa trên thời gian \\ \hline
UAT & User Acceptance Testing & Kiểm thử chấp nhận người dùng \\ \hline
UI / UX & User Interface / User Experience & Giao diện người dùng / Trải nghiệm người dùng \\ \hline
UUID & Universally Unique Identifier & Mã định danh duy nhất toàn cầu \\ \hline
\end{xltabular}
"""

ok2, msg2 = check_latex_balance(abbreviations)
print(f"Abbreviations Balance: {ok2} ({msg2})")
with open('c:/Users/Admin/Code/uniconnect-v2/bao-cao/Sections/0.8-Danh-muc-tu-viet-tat.tex', 'w', encoding='utf-8') as f:
    f.write(abbreviations)

print("Abstract and Abbreviations written successfully.")
