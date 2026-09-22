# -*- coding: utf-8 -*-
with open(r'bao-cao\scratch\generated_entities.tex', encoding='utf-8') as f:
    entities_text = f.read()

# Replace any remaining CLB / câu lạc bộ with Nhóm
entities_text = entities_text.replace("câu lạc bộ và đội nhóm", "đội nhóm")
entities_text = entities_text.replace("câu lạc bộ", "nhóm")
entities_text = entities_text.replace("CLB", "nhóm")

table_text = r"""\subsubsection{Mô tả các mối quan hệ thực thể}

\setlist[itemize]{leftmargin=*, nosep, topsep=0pt}

\begin{longtable}{|p{0.28\textwidth}|p{0.18\textwidth}|p{0.48\textwidth}|}
    \caption{Bảng tổng hợp các mối quan hệ giữa các thực thể nghiệp vụ (Domain Relationships)} \label{tab:relationship_summary} \\
    
    \hline
    \textbf{Thực thể tham gia} & \textbf{Quan hệ \& Lực lượng} & \textbf{Giải thích ý nghĩa \& Ràng buộc khóa ngoại (FK)} \\ \hline
    \endfirsthead

    \hline
    \textbf{Thực thể tham gia} & \textbf{Quan hệ \& Lực lượng} & \textbf{Giải thích ý nghĩa \& Ràng buộc khóa ngoại (FK)} \\ \hline
    \endhead

    \hline
    \endfoot

    \hline
    \endlastfoot

    \texttt{users} -- \texttt{activities} & Host / Own \newline (1 -- N) & 
    \begin{itemize}
        \item Một người dùng có thể tạo và chủ trì nhiều hoạt động ngoại khóa.
        \item Mỗi hoạt động bắt buộc có duy nhất một người chủ trì (\texttt{activities.host\_id} $\rightarrow$ \texttt{users.id}, ON DELETE CASCADE).
    \end{itemize} \\ \hline

    \texttt{groups} -- \texttt{activities} & Organize \newline (0..1 -- N) & 
    \begin{itemize}
        \item Một nhóm sinh viên có thể đứng tên chủ trì tổ chức nhiều sự kiện.
        \item Hoạt động có thể do một nhóm đứng tên hoặc do cá nhân tạo (\texttt{activities.group\_id} $\rightarrow$ \texttt{groups.id}, Nullable, ON DELETE SET NULL).
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{user\_follows} & Follow \newline (1 -- N) & 
    \begin{itemize}
        \item Một sinh viên có thể theo dõi nhiều người khác hoặc có nhiều người theo dõi.
        \item Khóa chính kép tự tham chiếu: \texttt{(follower\_id, following\_id)} trỏ về \texttt{users.id} (ON DELETE CASCADE).
    \end{itemize} \\ \hline
    
    \texttt{users} -- \texttt{activities} \newline (qua \texttt{join\_requests}) & Participate \newline (N -- N) & 
    \begin{itemize}
        \item Sinh viên đăng ký tham gia nhiều hoạt động; hoạt động có nhiều sinh viên tham gia.
        \item Thực thể trung gian \texttt{join\_requests} lưu trữ trạng thái duyệt đơn (\texttt{status}) và chứng nhận hoàn thành điểm danh (\texttt{attendance\_confirmed}). Ràng buộc: \texttt{UNIQUE(activity\_id, user\_id)}.
    \end{itemize} \\ \hline

    \texttt{activities} -- \texttt{groups} \newline (qua \texttt{activity\_cohosts}) & Co-host \newline (N -- N) & 
    \begin{itemize}
        \item Một hoạt động có thể liên kết đồng tổ chức với nhiều nhóm đối tác.
        \item Bảng \texttt{activity\_cohosts} cấp quyền ủy nhiệm mở điểm danh cho ban quản trị nhóm đối tác. Ràng buộc: \texttt{UNIQUE(activity\_id, group\_id)}.
    \end{itemize} \\ \hline

    \texttt{activities} -- \texttt{groups} \newline (qua \texttt{activity\_cohost\_invitations}) & Co-host Invite \newline (N -- N) & 
    \begin{itemize}
        \item Nhóm chủ trì (\texttt{host\_group\_id}) gửi lời mời đồng tổ chức sự kiện tới nhóm đối tác (\texttt{invited\_group\_id}).
        \item Lưu vết trạng thái phản hồi lời mời (\texttt{status}: pending, accepted, rejected).
    \end{itemize} \\ \hline

    \texttt{groups} -- \texttt{users} \newline (qua \texttt{group\_members}) & Member \newline (N -- N) & 
    \begin{itemize}
        \item Người dùng là thành viên của nhiều nhóm với vai trò xác định (\texttt{role}: admin, member). Quyền sở hữu nhóm do \texttt{groups.owner\_id} quản lý.
        \item Bảng \texttt{group\_members} ràng buộc: \texttt{UNIQUE(group\_id, user\_id)}.
    \end{itemize} \\ \hline

    \texttt{groups} -- \texttt{users} \newline (qua \texttt{group\_join\_requests}) & Join Group \newline (N -- N) & 
    \begin{itemize}
        \item Đơn đăng ký gia nhập nhóm từ sinh viên kèm câu trả lời khảo sát (\texttt{form\_responses}), quản lý theo trạng thái \texttt{status} (pending, approved, rejected).
        \item Ràng buộc: \texttt{UNIQUE(group\_id, user\_id)}.
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{organization\_verification\_requests} & Request Verification \newline (1 -- N) & 
    \begin{itemize}
        \item Sinh viên đại diện nhóm nộp hồ sơ minh chứng pháp lý xin cấp huy hiệu chính thức (\texttt{user\_id} $\rightarrow$ \texttt{users.id}).
        \item Quản trị viên thẩm định và phê duyệt lưu tại \texttt{reviewed\_by} $\rightarrow$ \texttt{users.id} (Nullable).
    \end{itemize} \\ \hline

    \texttt{activities} -- \texttt{trophies} & Reward \newline (1 -- N) & 
    \begin{itemize}
        \item Mỗi hoạt động có thể thiết lập các danh hiệu vinh danh trao tặng cho sinh viên hoàn thành (\texttt{trophies.activity\_id} $\rightarrow$ \texttt{activities.id}, ON DELETE CASCADE).
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{trophies} \newline (qua \texttt{user\_trophies}) & Achieve / Earn \newline (N -- N) & 
    \begin{itemize}
        \item Người dùng tích lũy nhiều danh hiệu \texttt{trophies}; danh hiệu được trao cho nhiều sinh viên.
        \item Bảng \texttt{user\_trophies} lưu mốc thời gian trao tặng và hoạt động đạt được (\texttt{activity\_id}), ràng buộc \texttt{UNIQUE(user\_id, trophy\_id)}.
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{user\_busy\_slots} & Busy Schedule \newline (1 -- N) & 
    \begin{itemize}
        \item Sinh viên cấu hình các khung giờ bận trong tuần (lịch học cố định, ca trực) phục vụ phát hiện xung đột thời gian (\texttt{user\_id} $\rightarrow$ \texttt{users.id}, ON DELETE CASCADE).
    \end{itemize} \\ \hline

    \texttt{user\_busy\_slots} -- \texttt{busy\_slot\_exceptions} & Has Exception \newline (1 -- N) & 
    \begin{itemize}
        \item Một khung giờ bận định kỳ có thể có các ngày ngoại lệ nghỉ lễ hoặc dời buổi học (\texttt{busy\_slot\_id} $\rightarrow$ \texttt{user\_busy\_slots.id}, ON DELETE CASCADE).
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{user\_vacation\_periods} & Vacation \newline (1 -- N) & 
    \begin{itemize}
        \item Sinh viên quản lý các kỳ nghỉ dài ngày (\texttt{start\_date <= end\_date}) để hệ thống tạm ngắt cảnh báo bận (\texttt{user\_id} $\rightarrow$ \texttt{users.id}, ON DELETE CASCADE).
    \end{itemize} \\ \hline

    \texttt{activities} -- \texttt{custom\_forms} & Has Form \newline (0..1 -- 1) & 
    \begin{itemize}
        \item Hoạt động có thể liên kết với một biểu mẫu đăng ký tùy biến (\texttt{activities.custom\_form\_id} $\rightarrow$ \texttt{custom\_forms.id}, Nullable, ON DELETE SET NULL).
    \end{itemize} \\ \hline

    \texttt{groups} -- \texttt{custom\_forms} & Has Form \newline (0..1 -- 1) & 
    \begin{itemize}
        \item Nhóm có thể liên kết với một biểu mẫu tuyển thành viên tùy biến (\texttt{groups.custom\_form\_id} $\rightarrow$ \texttt{custom\_forms.id}, Nullable, ON DELETE SET NULL).
    \end{itemize} \\ \hline

    \texttt{custom\_forms} -- \texttt{form\_fields} & Contains \newline (1 -- N) & 
    \begin{itemize}
        \item Biểu mẫu tùy biến chứa nhiều câu hỏi và trường nhập liệu (\texttt{form\_fields.form\_id} $\rightarrow$ \texttt{custom\_forms.id}, ON DELETE CASCADE).
    \end{itemize} \\ \hline

    \texttt{activities} -- \texttt{comments} & Discussion \newline (1 -- N) & 
    \begin{itemize}
        \item Hoạt động chứa luồng thảo luận gồm nhiều bình luận của sinh viên (\texttt{comments.activity\_id} $\rightarrow$ \texttt{activities.id}, ON DELETE CASCADE).
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{comments} & Author \newline (1 -- N) & 
    \begin{itemize}
        \item Người dùng đăng tải nhiều bình luận trao đổi trong các hoạt động (\texttt{comments.user\_id} $\rightarrow$ \texttt{users.id}, ON DELETE CASCADE).
    \end{itemize} \\ \hline

    \texttt{comments} -- \texttt{comments} & Reply \newline (1 -- N) & 
    \begin{itemize}
        \item Mối quan hệ tự thân hỗ trợ cấu trúc thảo luận phân cấp lồng nhau đa tầng (\texttt{comments.parent\_id} $\rightarrow$ \texttt{comments.id}, Nullable, ON DELETE CASCADE).
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{notifications} & Receive \newline (1 -- N) & 
    \begin{itemize}
        \item Người dùng nhận được nhiều thông báo hệ thống và tương tác theo thời gian thực (\texttt{notifications.user\_id} $\rightarrow$ \texttt{users.id}, ON DELETE CASCADE).
        \item Thông báo liên kết tùy chọn với hoạt động (\texttt{activity\_id} $\rightarrow$ \texttt{activities.id}, ON DELETE SET NULL) và điều hướng động qua \texttt{action\_url}.
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{reports} & File Report \newline (1 -- N) & 
    \begin{itemize}
        \item Người dùng gửi nhiều báo cáo vi phạm nội dung (\texttt{reporter\_id} $\rightarrow$ \texttt{users.id}, ON DELETE CASCADE).
        \item Trường \texttt{target\_type} và \texttt{target\_id} sử dụng cơ chế định danh đa hình (Polymorphic Reference).
        \item Quản trị viên xử lý lưu tại \texttt{resolved\_by} $\rightarrow$ \texttt{users.id} (Nullable, ON DELETE SET NULL).
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{content\_likes} & Like Activity \newline (1 -- N) & 
    \begin{itemize}
        \item Người dùng bày tỏ cảm xúc yêu thích hoạt động ngoại khóa. Ràng buộc khóa ngoại trực tiếp \texttt{content\_likes.activity\_id} ($\rightarrow$ \texttt{activities.id}, ON DELETE CASCADE) và \texttt{UNIQUE(activity\_id, user\_id)}.
    \end{itemize} \\ \hline

    \texttt{users} -- \texttt{admin\_audit\_logs} & Audit Trail \newline (1 -- N) & 
    \begin{itemize}
        \item Lưu vết chi tiết từng thao tác quản trị viên phục vụ giám sát và kiểm toán bảo mật (\texttt{admin\_audit\_logs.actor\_id} $\rightarrow$ \texttt{users.id}, ON DELETE SET NULL).
    \end{itemize} \\ \hline
\end{longtable}
"""

full_replacement = entities_text.strip() + "\n\n" + table_text.strip()
with open(r'bao-cao\scratch\full_replacement.tex', 'w', encoding='utf-8') as f:
    f.write(full_replacement)
print("Full replacement prepared.")
