import sys
sys.stdout.reconfigure(encoding='utf-8')
from test_diagrams import check_latex_balance

ui_section = r"""\subsection{Hiện thực giao diện người dùng (User Interface - Frontend)}
Giao diện người dùng của UniConnect được xây dựng bằng thư viện React 18 kết hợp ngôn ngữ TypeScript và công cụ đóng gói Vite. Thiết kế giao diện tuân thủ triết lý tối giản, hiện đại với bộ biểu tượng chuẩn Lucide Icons, cấu trúc lưới linh hoạt (Responsive Grid) đảm bảo trải nghiệm tương thích hoàn hảo trên cả trình duyệt máy tính để bàn lẫn thiết bị di động (Mobile-first). Dưới đây là các màn hình chức năng then chốt của hệ thống:

\subsubsection{1. Màn hình Bản đồ Khám phá Hoạt động (Campus Interactive Map)}
Giao diện trung tâm cho phép sinh viên tương tác trực tiếp với bản đồ khuôn viên trường. Các hoạt động được phân loại theo màu sắc biểu tượng trực quan, hỗ trợ định vị GPS thời gian thực và lọc sự kiện theo bán kính di chuyển.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.88\textwidth]{Images/ui-campus-map.png}
    \caption{Giao diện Bản đồ khám phá hoạt động học đường tương tác}
    \label{fig:ui_campus_map}
\end{figure}

\subsubsection{2. Màn hình Chi tiết Hoạt động và Đăng ký tham gia (Event Details)}
Cung cấp thông tin đầy đủ về sự kiện: thời gian, địa điểm, đơn vị chủ trì, các câu lạc bộ Đồng tổ chức (Co-hosts), số suất tham dự còn lại và tự động đối soát lịch trình cá nhân để đưa ra cảnh báo trùng lịch nếu có.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.88\textwidth]{Images/ui-activity-detail.png}
    \caption{Giao diện Chi tiết hoạt động và đối soát lịch trình đăng ký}
    \label{fig:ui_activity_detail}
\end{figure}

\subsubsection{3. Màn hình Điểm danh Đa chế độ (Multi-mode Attendance)}
Hỗ trợ hai cơ chế xác thực hiện đại: Quét mã QR xoay động 30 giây HMAC-SHA256 trên màn hình ban tổ chức, hoặc nhấn nút xác nhận Radar GPS 1-Chạm khi sinh viên đã có mặt trong bán kính quy định của hội trường.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.88\textwidth]{Images/ui-attendance-checkin.png}
    \caption{Giao diện Điểm danh chống gian lận đa chế độ (HMAC QR và GPS)}
    \label{fig:ui_attendance_checkin}
\end{figure}

\subsubsection{4. Màn hình Lịch Thông minh (Smart Calendar Schedule)}
Hiển thị tổng thể lịch trình cá nhân của sinh viên theo dạng tuần/tháng, tích hợp các khung giờ bận cố định (thời khóa biểu) và các sự kiện ngoại khóa đã xác nhận tham gia. Hỗ trợ nút xuất nhanh file chuẩn \texttt{.ics} để đồng bộ với Google Calendar hoặc Apple Calendar.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.88\textwidth]{Images/ui-smart-calendar.png}
    \caption{Giao diện Lịch thông minh và quản lý khung giờ bận cá nhân}
    \label{fig:ui_smart_calendar}
\end{figure}

\subsubsection{5. Màn hình Hồ sơ Cá nhân và Bộ sưu tập Danh hiệu (Gamification Profile)}
Không gian tôn vinh nỗ lực rèn luyện của sinh viên: hiển thị số ngày Công tác Xã hội (CTXH) tích lũy, điểm rèn luyện, cấp bậc thứ hạng sinh viên và tủ trưng bày các danh hiệu Trophy đã mở khóa.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.88\textwidth]{Images/ui-gamification-profile.png}
    \caption{Giao diện Hồ sơ cá nhân, tiến trình tích lũy CTXH và danh hiệu Trophy}
    \label{fig:ui_gamification_profile}
\end{figure}

\subsubsection{6. Màn hình Trợ lý Học đường AI (AI Assistant Chat)}
Giao diện trao đổi tương tác với trợ lý thông minh theo kiến trúc RAG: sinh viên có thể đặt câu hỏi về quy định ngày CTXH, nhờ tìm kiếm các hoạt động phù hợp với sở thích hoặc kiểm tra khung thời gian rảnh trong tuần.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.88\textwidth]{Images/ui-ai-assistant.png}
    \caption{Giao diện Trợ lý học đường AI giải đáp quy chế và gợi ý sự kiện}
    \label{fig:ui_ai_assistant}
\end{figure}

\subsubsection{7. Màn hình Bảng điều khiển Quản trị viên (Admin KPI Dashboard)}
Dành riêng cho ban điều hành trường học: theo dõi các biểu đồ trực quan về mức độ tăng trưởng người dùng, tỷ lệ tham gia phong trào, kiểm duyệt các báo cáo vi phạm nội dung và xuất danh sách sinh viên chuẩn UTF-8 BOM CSV.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.88\textwidth]{Images/ui-admin-dashboard.png}
    \caption{Giao diện Bảng điều khiển Quản trị viên và Kiểm duyệt nội dung}
    \label{fig:ui_admin_dashboard}
\end{figure}

\subsubsection{8. Màn hình Tra cứu Xác thực Chứng nhận (Certificate Verification)}
Cổng thông tin mở tại đường dẫn \texttt{/verify-certificate} cho phép bất kỳ ai (nhà tuyển dụng, ban thi đua) quét mã QR trên Giấy chứng nhận điện tử để tra cứu tính nguyên bản và thông tin xác thực từ máy chủ UniConnect.

\begin{figure}[H]
    \centering
    \includegraphics[width=0.88\textwidth]{Images/ui-certificate-verify.png}
    \caption{Giao diện Cổng tra cứu xác thực Giấy chứng nhận CTXH trực tuyến}
    \label{fig:ui_certificate_verify}
\end{figure}
"""

ok, msg = check_latex_balance(ui_section)
print(f"UI Section Balance: {ok} ({msg})")

# Read Section 6
with open('c:/Users/Admin/Code/uniconnect-v2/bao-cao/Sections/6-Hien-thuc-backend.tex', encoding='utf-8') as f:
    s6 = f.read()

# Replace \subsection{Kết luận chương} with ui_section + \subsection{Kết luận chương}
target = r"\subsection{Kết luận chương}"
idx = s6.find(target)
if idx != -1:
    new_s6 = s6[:idx] + ui_section + "\n" + s6[idx:]
    with open('c:/Users/Admin/Code/uniconnect-v2/bao-cao/Sections/6-Hien-thuc-backend.tex', 'w', encoding='utf-8') as f:
        f.write(new_s6)
    print("Section 6 updated with UI section successfully.")
else:
    print("Target not found in Section 6.")
