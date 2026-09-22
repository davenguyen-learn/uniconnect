import sys
import re

def check_latex_balance(text):
    stack = []
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        line_no_comment = re.sub(r'(?<!\\)%.*$', '', line)
        for j, char in enumerate(line_no_comment):
            if char in '{[(':
                stack.append((char, i, j+1))
            elif char in '}])':
                if not stack:
                    return False, f"Extra closing '{char}' at line {i}:{j+1}"
                opening, oi, oj = stack.pop()
                expected = {'{':'}', '[':']', '(':')'}[opening]
                if char != expected:
                    return False, f"Mismatched pair: '{opening}' at line {oi}:{oj} closed by '{char}' at line {i}:{j+1}"
    if stack:
        opening, oi, oj = stack[-1]
        return False, f"Unclosed '{opening}' from line {oi}:{oj}"
    return True, "Balanced"

# Diagram 1: Multi-mode Attendance Activity
diagram1 = r"""
\begin{figure}[H]
\centering
\resizebox{0.92\textwidth}{!}{
\begin{tikzpicture}[
    >=Stealth,
    node distance=1.1cm and 1.5cm,
    startstop/.style={rectangle, rounded corners=12pt, minimum width=2.8cm, minimum height=0.9cm, text centered, draw=blue!80!black, fill=blue!10, font=\bfseries\small},
    decision/.style={diamond, aspect=2, minimum width=2.6cm, minimum height=1cm, text centered, draw=orange!90!black, fill=orange!15, font=\small},
    process/.style={rectangle, rounded corners=3pt, minimum width=3.4cm, minimum height=0.9cm, text centered, draw=blue!70!black, fill=blue!5, font=\small},
    reject/.style={rectangle, rounded corners=3pt, minimum width=2.8cm, minimum height=0.8cm, text centered, draw=red!80!black, fill=red!10, font=\small},
    line/.style={draw, thick, ->}
]

\node (start) [startstop] {Bắt đầu điểm danh};
\node (mode) [decision, below=0.8cm of start] {Phương thức?};

\node (qr_gen) [process, below left=1.0cm and 0.8cm of mode] {BTC: Tạo mã QR xoay động\\(HMAC-SHA256, 30s)};
\node (qr_scan) [process, below=0.8cm of qr_gen] {Sinh viên: Quét mã QR\\Gửi token lên Server};

\node (gps_req) [process, below right=1.0cm and 0.8cm of mode] {BTC: Mở phiên điểm danh\\Radar GPS 1-Chạm};
\node (gps_loc) [process, below=0.8cm of gps_req] {Sinh viên: Gửi tọa độ GPS\\$(lat, lng, accuracy)$};

\node (untrusted) [decision, below=3.6cm of mode] {Kiểm tra đăng ký\\\& Khung giờ sự kiện?};
\node (rej_reg) [reject, right=2.0cm of untrusted] {Từ chối: Không hợp lệ\\hoặc hết giờ};

\node (verify_method) [decision, below=1.0cm of untrusted] {Loại xác thực?};

\node (chk_hmac) [decision, below left=1.0cm and 0.5cm of verify_method] {HMAC hợp lệ?\\($\Delta t \le 30$s)};
\node (rej_hmac) [reject, left=1.2cm of chk_hmac] {Từ chối: Token sai\\hoặc quá hạn};

\node (chk_gps) [decision, below right=1.0cm and 0.5cm of verify_method] {Khoảng cách $\le R$?\\\& $acc \le 50$m};
\node (rej_gps) [reject, right=1.2cm of chk_gps] {Từ chối: Ngoài bán kính\\hoặc GPS sai số};

\node (chk_dup) [decision, below=2.6cm of verify_method] {Đã điểm danh\\trước đó chưa?};
\node (rej_dup) [reject, right=2.0cm of chk_dup] {Từ chối: Đã ghi nhận\\tránh trùng lặp};

\node (record) [process, below=1.0cm of chk_dup] {Cập nhật trạng thái: Đã tham gia\\(attendance\_confirmed = True)};
\node (gamify) [process, below=0.8cm of record] {Kích hoạt Gamification:\\Tích lũy CTXH, xét danh hiệu};
\node (finish) [startstop, below=0.8cm of gamify] {Hoàn tất điểm danh};

\path [line] (start) -- (mode);
\path [line] (mode) -| node[above, font=\scriptsize] {Mã QR} (qr_gen);
\path [line] (qr_gen) -- (qr_scan);
\path [line] (qr_scan) |- (untrusted);

\path [line] (mode) -| node[above, font=\scriptsize] {GPS Radar} (gps_req);
\path [line] (gps_req) -- (gps_loc);
\path [line] (gps_loc) |- (untrusted);

\path [line] (untrusted) -- node[above, font=\scriptsize] {Không} (rej_reg);
\path [line] (untrusted) -- node[right, font=\scriptsize] {Hợp lệ} (verify_method);

\path [line] (verify_method) -| node[above, font=\scriptsize] {QR} (chk_hmac);
\path [line] (chk_hmac) -- node[above, font=\scriptsize] {Sai} (rej_hmac);
\path [line] (chk_hmac) |- node[near start, left, font=\scriptsize] {Đúng} (chk_dup);

\path [line] (verify_method) -| node[above, font=\scriptsize] {GPS} (chk_gps);
\path [line] (chk_gps) -- node[above, font=\scriptsize] {Vượt ngưỡng} (rej_gps);
\path [line] (chk_gps) |- node[near start, right, font=\scriptsize] {Đạt} (chk_dup);

\path [line] (chk_dup) -- node[above, font=\scriptsize] {Đã có} (rej_dup);
\path [line] (chk_dup) -- node[right, font=\scriptsize] {Chưa} (record);

\path [line] (record) -- (gamify);
\path [line] (gamify) -- (finish);

\end{tikzpicture}
}
\caption{Activity Diagram: Quy trình điểm danh chống gian lận đa chế độ (HMAC QR và Geofencing)}
\label{fig:activity_diem_danh_da_che_do}
\end{figure}
"""

# Diagram 2: Attendance -> Gamification Sequence
diagram2 = r"""
\begin{figure}[H]
\centering
\resizebox{0.95\textwidth}{!}{
\begin{tikzpicture}[
    >=Stealth,
    font=\footnotesize,
    lifeline/.style={draw=gray!70, dashed, thick},
    actor/.style={rectangle, rounded corners=3pt, draw=blue!80!black, fill=blue!15, minimum width=2.2cm, minimum height=0.8cm, font=\bfseries\footnotesize, align=center},
    msg/.style={->, thick, >=stealth},
    reply/.style={<--, dashed, thick, >=stealth},
    note/.style={rectangle, draw=orange!80!black, fill=orange!10, rounded corners=2pt, font=\scriptsize, align=left}
]

% Lifelines coordinates
\node[actor] (student) at (0,0) {Sinh viên\\(Client SPA)};
\node[actor] (router) at (3.2,0) {Attendance\\Router};
\node[actor] (att_svc) at (6.4,0) {Attendance\\Service};
\node[actor] (gam_svc) at (9.8,0) {Gamification\\Service};
\node[actor] (db) at (13.2,0) {PostgreSQL\\(Database)};

% Vertical Lifelines
\draw[lifeline] (student) -- (0,-9.5);
\draw[lifeline] (router) -- (3.2,-9.5);
\draw[lifeline] (att_svc) -- (6.4,-9.5);
\draw[lifeline] (gam_svc) -- (9.8,-9.5);
\draw[lifeline] (db) -- (13.2,-9.5);

% Messages
\draw[msg] (0,-1.0) -- node[above] {1. POST /attendance/check-in} (3.2,-1.0);
\draw[msg] (3.2,-1.6) -- node[above] {2. verify\_and\_check\_in(payload)} (6.4,-1.6);

\draw[msg] (6.4,-2.2) -- node[above] {3. SELECT reg, activity WHERE id} (13.2,-2.2);
\draw[reply] (6.4,-2.7) -- node[above] {4. Trả về thông tin đăng ký} (13.2,-2.7);

\node[note, right=0.1cm of att_svc] at (6.5,-3.4) {5. Xác thực Invariant:\\- Khung giờ hợp lệ\\- HMAC 30s hoặc Geofence\\- Chưa điểm danh};

\draw[msg] (6.4,-4.3) -- node[above] {6. UPDATE attendance\_confirmed=True} (13.2,-4.3);
\draw[reply] (6.4,-4.8) -- node[above] {7. Xác nhận cập nhật thành công} (13.2,-4.8);

\draw[msg] (6.4,-5.4) -- node[above] {8. award\_attendance\_rewards(user, act)} (9.8,-5.4);

\node[note, right=0.1cm of gam_svc] at (9.9,-6.1) {9. Xử lý Gamification:\\- Cộng tích lũy CTXH\\- Đối soát mốc danh hiệu\\- Cập nhật thứ hạng};

\draw[msg] (9.8,-7.0) -- node[above] {10. INSERT Trophy, UPDATE CTXH} (13.2,-7.0);
\draw[reply] (9.8,-7.5) -- node[above] {11. Transaction Commit OK} (13.2,-7.5);

\draw[reply] (6.4,-8.0) -- node[above] {12. Trả về kết quả Gamification} (9.8,-8.0);
\draw[reply] (3.2,-8.5) -- node[above] {13. 200 OK (CTXH earned, Trophy unlocked)} (6.4,-8.5);
\draw[reply] (0,-9.0) -- node[above] {14. Hiển thị thông báo thành công \& hiệu ứng nhận giải} (3.2,-9.0);

\end{tikzpicture}
}
\caption{Sequence Diagram: Luồng tích hợp xác thực điểm danh và phân bổ phần thưởng Gamification}
\label{fig:sequence_diem_danh_gamification}
\end{figure}
"""

# Diagram 3: Smart Calendar Conflict Detection Flowchart
diagram3 = r"""
\begin{figure}[H]
\centering
\resizebox{0.88\textwidth}{!}{
\begin{tikzpicture}[
    >=Stealth,
    node distance=1.1cm and 1.5cm,
    startstop/.style={rectangle, rounded corners=12pt, minimum width=3.2cm, minimum height=0.9cm, text centered, draw=blue!80!black, fill=blue!10, font=\bfseries\small},
    decision/.style={diamond, aspect=2.2, minimum width=3.2cm, minimum height=1cm, text centered, draw=orange!90!black, fill=orange!15, font=\small},
    process/.style={rectangle, rounded corners=3pt, minimum width=3.8cm, minimum height=0.9cm, text centered, draw=blue!70!black, fill=blue!5, font=\small},
    outcome_hard/.style={rectangle, rounded corners=3pt, minimum width=3.6cm, minimum height=0.8cm, text centered, draw=red!80!black, fill=red!15, font=\small\bfseries},
    outcome_soft/.style={rectangle, rounded corners=3pt, minimum width=3.6cm, minimum height=0.8cm, text centered, draw=orange!80!black, fill=orange!15, font=\small\bfseries},
    outcome_none/.style={rectangle, rounded corners=3pt, minimum width=3.6cm, minimum height=0.8cm, text centered, draw=green!70!black, fill=green!15, font=\small\bfseries},
    line/.style={draw, thick, ->}
]

\node (start) [startstop] {Bắt đầu đối soát xung đột lịch};
\node (input) [process, below=0.8cm of start] {Nhận sự kiện ứng viên $E_c$ ($s_c \le t < e_c$)\\và danh sách sự kiện đã có $E_i$ ($s_i \le t < e_i$)};

\node (overlap) [decision, below=1.0cm of input] {$\max(s_c, s_i) < \min(e_c, e_i)$?};

\node (hard) [outcome_hard, right=1.6cm of overlap] {Xung đột cứng (Hard Conflict):\\Trùng lặp thời gian tham gia};

\node (adjacent) [decision, below=1.2cm of overlap] {$\min(e_c, e_i) = \max(s_c, s_i)$?\\(Liền kề biên mút)};

\node (buffer) [decision, below=1.2cm of adjacent] {Khoảng đệm $\Delta t < 15$ phút?\\($0 < \Delta t < 15$m)};

\node (soft) [outcome_soft, right=1.6cm of buffer] {Xung đột mềm (Soft Conflict):\\Cảnh báo sát giờ di chuyển};

\node (clear) [outcome_none, below=1.0cm of buffer] {Không xung đột (No Conflict):\\Lịch trình hoàn toàn khả thi};

\node (return_meta) [process, below=1.0cm of clear] {Trả về kết quả kiểm tra kèm cờ cảnh báo\\(Bảo toàn trạng thái dữ liệu - Non-mutating)};

\path [line] (start) -- (input);
\path [line] (input) -- (overlap);
\path [line] (overlap) -- node[above, font=\scriptsize] {Đúng (Giao nhau)} (hard);
\path [line] (overlap) -- node[right, font=\scriptsize] {Sai (Không giao)} (adjacent);
\path [line] (adjacent) -- node[above, font=\scriptsize] {Đúng (Liền kề)} (soft);
\path [line] (adjacent) -- node[right, font=\scriptsize] {Sai ($\Delta t > 0$)} (buffer);
\path [line] (buffer) -- node[above, font=\scriptsize] {Đúng} (soft);
\path [line] (buffer) -- node[right, font=\scriptsize] {Sai ($\Delta t \ge 15$m)} (clear);
\path [line] (clear) -- (return_meta);
\path [line] (hard) |- (return_meta);
\path [line] (soft) |- (return_meta);

\end{tikzpicture}
}
\caption{Flowchart: Thuật toán phát hiện xung đột lịch dựa trên vị từ giao nhau thời gian}
\label{fig:flowchart_phat_hien_xung_dot_lich}
\end{figure}
"""

# Diagram 4: Groups / Co-host RBAC Flow
diagram4 = r"""
\begin{figure}[H]
\centering
\resizebox{0.92\textwidth}{!}{
\begin{tikzpicture}[
    >=Stealth,
    font=\footnotesize,
    lifeline/.style={draw=gray!70, dashed, thick},
    actor/.style={rectangle, rounded corners=3pt, draw=blue!80!black, fill=blue!15, minimum width=2.3cm, minimum height=0.8cm, font=\bfseries\footnotesize, align=center},
    msg/.style={->, thick, >=stealth},
    reply/.style={<--, dashed, thick, >=stealth},
    note/.style={rectangle, draw=orange!80!black, fill=orange!10, rounded corners=2pt, font=\scriptsize, align=left}
]

% Participants
\node[actor] (owner) at (0,0) {CLB Chủ trì\\(Primary Owner)};
\node[actor] (cohost) at (3.5,0) {CLB Đồng tổ chức\\(Co-host Club)};
\node[actor] (router) at (7.0,0) {Groups \& Co-host\\Router};
\node[actor] (rbac) at (10.5,0) {RBAC Permissions\\Engine};
\node[actor] (db) at (13.8,0) {PostgreSQL\\(Database)};

% Vertical Lifelines
\draw[lifeline] (owner) -- (0,-9.0);
\draw[lifeline] (cohost) -- (3.5,-9.0);
\draw[lifeline] (router) -- (7.0,-9.0);
\draw[lifeline] (rbac) -- (10.5,-9.0);
\draw[lifeline] (db) -- (13.8,-9.0);

% Sequence
\draw[msg] (0,-1.0) -- node[above] {1. POST /activities/{id}/co-hosts (target\_group\_id)} (7.0,-1.0);
\draw[msg] (7.0,-1.5) -- node[above] {2. can\_invite\_cohost(user, activity)} (10.5,-1.5);
\draw[reply] (7.0,-2.0) -- node[above] {3. Quyền hợp lệ (Primary Owner)} (10.5,-2.0);
\draw[msg] (7.0,-2.5) -- node[above] {4. INSERT CoHostInvitation (status=PENDING)} (13.8,-2.5);

\draw[msg] (3.5,-3.6) -- node[above] {5. PUT /co-hosts/{invite\_id}/accept} (7.0,-3.6);
\draw[msg] (7.0,-4.1) -- node[above] {6. UPDATE CoHostInvitation (status=ACCEPTED)} (13.8,-4.1);

\node[note] at (7.0,-5.1) {7. Thiết lập liên kết Đồng tổ chức:\\Co-host được cấp quyền ủy nhiệm trên sự kiện};

\draw[msg] (3.5,-6.2) -- node[above] {8. POST /activities/{id}/check-in/open} (7.0,-6.2);
\draw[msg] (7.0,-6.7) -- node[above] {9. can\_open\_checkin(user, activity)} (10.5,-6.7);
\draw[reply] (7.0,-7.2) -- node[above] {10. Phê chuẩn (Thuộc nhóm Co-host đã duyệt)} (10.5,-7.2);

\draw[msg] (7.0,-7.8) -- node[above] {11. Mở phiên điểm danh sự kiện thành công} (13.8,-7.8);
\draw[reply] (3.5,-8.4) -- node[above] {12. 200 OK: Phiên điểm danh đã được kích hoạt} (7.0,-8.4);

\end{tikzpicture}
}
\caption{Sequence Diagram: Quy trình phân quyền ủy nhiệm Đồng tổ chức (Co-hosting RBAC)}
\label{fig:sequence_cohost_rbac}
\end{figure}
"""

# Diagram 5: Production Container Deployment Architecture
diagram5 = r"""
\begin{figure}[H]
\centering
\resizebox{0.92\textwidth}{!}{
\begin{tikzpicture}[
    >=Stealth,
    node distance=0.9cm and 1.2cm,
    clientbox/.style={rectangle, rounded corners=6pt, draw=blue!80!black, fill=blue!10, minimum width=13.0cm, minimum height=1.2cm, align=center, font=\small},
    ingressbox/.style={rectangle, rounded corners=6pt, draw=orange!80!black, fill=orange!15, minimum width=13.0cm, minimum height=1.1cm, align=center, font=\small},
    dockerbound/.style={rectangle, rounded corners=8pt, draw=gray!70, dashed, fill=gray!4, inner sep=15pt},
    nginxbox/.style={rectangle, rounded corners=5pt, draw=teal!80!black, fill=teal!10, minimum width=12.2cm, minimum height=1.8cm, align=left, font=\small},
    fastapibox/.style={rectangle, rounded corners=5pt, draw=purple!80!black, fill=purple!10, minimum width=12.2cm, minimum height=2.3cm, align=left, font=\small},
    dbbox/.style={rectangle, rounded corners=5pt, draw=blue!70!black, fill=blue!10, minimum width=12.2cm, minimum height=1.8cm, align=left, font=\small},
    netline/.style={draw=blue!80!black, very thick, <->},
    flowline/.style={draw=black, thick, ->}
]

% Top: Users & Public Internet
\node (internet) [clientbox] {\textbf{Internet / Người dùng cuối} (Web Browser / Thiết bị di động)};

% External Ingress
\node (ingress) [ingressbox, below=1.0cm of internet] {\textbf{External Ingress / TLS Termination} (Cloudflare / AWS ALB / Reverse Proxy Ingress)\\$\blacktriangleright$ Phục vụ HTTPS (Port 443) $\rightarrow$ Giải mã SSL/TLS $\rightarrow$ Chuyển tiếp HTTP nội bộ (Port 80)};

% Docker Network Boundary
\node (nginx) [nginxbox, below=1.5cm of ingress] {
    \textbf{Container: \texttt{client} (Nginx 1.27-alpine)} --- Phục vụ cổng 80 nội bộ\\
    $\bullet$ \textbf{SPA Hosting:} Cung cấp bundle React 18, Vite, Lucide Icons đã tối ưu hóa\\
    $\bullet$ \textbf{Caching tĩnh:} \texttt{Cache-Control: public, max-age=31536000, immutable} cho \texttt{/assets/*}\\
    $\bullet$ \textbf{Security Headers:} \texttt{X-Frame-Options DENY}, \texttt{X-Content-Type-Options nosniff}\\
    $\bullet$ \textbf{Reverse Proxy:} Điều hướng \texttt{/api/*} tới \texttt{http://server:8000} kèm \texttt{X-Real-IP}, \texttt{X-Forwarded-For}
};

\node (fastapi) [fastapibox, below=1.2cm of nginx] {
    \textbf{Container: \texttt{server} (FastAPI / Uvicorn)} --- Phục vụ cổng 8000 nội bộ (Không mở public)\\
    $\bullet$ \textbf{Đặc quyền tối thiểu:} Vận hành dưới người dùng non-root (\texttt{appuser:1001})\\
    $\bullet$ \textbf{Application-Layer Rate Limiting:} Giới hạn tần suất truy vấn tầng ứng dụng (\texttt{chat/router.py})\\
    $\bullet$ \textbf{Xác thực \& Phân quyền:} Kiểm tra chữ ký số JWT, phân quyền vai trò RBAC và Co-hosting\\
    $\bullet$ \textbf{Nghiệp vụ cốt lõi:} Điểm danh HMAC 30s \& Geofencing; Smart Calendar đối soát xung đột; Gamification; RAG
};

\node (db) [dbbox, below=1.2cm of fastapi] {
    \textbf{Container: \texttt{db} (PostgreSQL 16)} --- Phục vụ cổng 5432 nội bộ (Mạng Docker cục bộ)\\
    $\bullet$ \textbf{Hình ảnh nền tảng:} \texttt{postgis/postgis:16-3.4} kèm tiện ích không gian PostGIS và pgvector\\
    $\bullet$ \textbf{Quản lý kết nối:} SQLAlchemy AsyncPG Connection Pool (\texttt{pool\_size=20, max\_overflow=10})\\
    $\bullet$ \textbf{Lưu trữ bền vững:} Docker Named Volume (\texttt{db\_data}) lưu trữ dữ liệu an toàn
};

% Background docker boundary
    \node [dockerbound, fit=(nginx) (fastapi) (db), label={[anchor=north west, font=\bfseries\footnotesize, text=gray!80]{Mạng nội bộ Docker Bridge (\texttt{uniconnect\_net}) --- Môi trường Production Đóng kín}}] {};

% Connecting arrows
\path [flowline] (internet) -- node[right, font=\scriptsize\bfseries] {HTTPS (443)} (ingress);
\path [flowline] (ingress) -- node[right, font=\scriptsize\bfseries] {HTTP (80)} (nginx);
\path [flowline] (nginx) -- node[right, font=\scriptsize\bfseries] {HTTP Proxy (8000)} (fastapi);
\path [flowline] (fastapi) -- node[right, font=\scriptsize\bfseries] {AsyncPG Connection Pool (5432)} (db);

\end{tikzpicture}
}
\caption{Kiến trúc triển khai container hệ thống UniConnect trên môi trường Production}
\label{fig:kien_truc_trien_khai_production}
\end{figure}
"""

all_diagrams = [("Diagram 1", diagram1), ("Diagram 2", diagram2), ("Diagram 3", diagram3), ("Diagram 4", diagram4), ("Diagram 5", diagram5)]

for name, d in all_diagrams:
    ok, msg = check_latex_balance(d)
    print(f"{name}: {ok} ({msg})")
