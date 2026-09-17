# BẢN ĐẶC TẢ THIẾT KẾ UI/UX TOÀN DIỆN HỆ THỐNG UNICONNECT
> **Vai trò:** Senior UI/UX & Design System Architect (10+ năm kinh nghiệm)  
> **Dự án:** UniConnect (Web Responsive & Mobile App Native Feel)  
> **Mục tiêu:** Nâng tầm trải nghiệm người dùng từ nghiệp dư thành một sản phẩm công nghệ giáo dục đẳng cấp quốc tế: Trực quan, Sang trọng, Hiện đại, Tối ưu cho cả Sinh viên mới (New User) đến Ban tổ chức/Quản trị viên (Super User).  
> **File tài liệu:** `THIET_KE_UI_UX_UNICONNECT.md`

---

## MỤC LỤC
1. [TRIẾT LÝ THIẾT KẾ & HỆ THỐNG THIẾT KẾ (DESIGN SYSTEM)](#1-triết-lý-thiết-kế--hệ-thống-thiết-kế-design-system)
2. [PHÂN KHÚC NGƯỜI DÙNG & CHIẾN LƯỢC THIẾT KẾ THÍCH ỨNG (USER PERSONAS & ADAPTIVE UX)](#2-phân-khúc-người-dùng--chiến-lược-thiết-kế-thích-ứng)
3. [KIẾN TRÚC GIAO DIỆN ĐA NỀN TẢNG (DESKTOP WEB VS. MOBILE APP NATIVE)](#3-kiến-trúc-giao-diện-đa-nền-tảng-desktop-web-vs-mobile-app-native)
4. [ĐẶC TẢ CHI TIẾT TỪNG MÀN HÌNH CỐT LÕI (PAGE-BY-PAGE SPECS)](#4-đặc-tả-chi-tiết-từng-màn-hình-cốt-lõi-page-by-page-specs)
   - [4.1. Trang Chủ / Khám Phá Sự Kiện (Discovery & Dashboard)](#41-trang-chủ--khám-phá-sự-kiện-discovery--dashboard)
   - [4.2. Trang Chi Tiết Hoạt Động & Đăng Ký (Activity Detail & Dynamic Form)](#42-trang-chi-tiết-hoạt-động--đăng-ký-activity-detail--dynamic-form)
   - [4.3. Trải Nghiệm Điểm Danh Radar GPS 1-Chạm (Proximity Radar Attendance UX)](#43-trải-nghiệm-điểm-danh-radar-gps-1-chạm-proximity-radar-attendance-ux)
   - [4.4. Giấy Chứng Nhận CTXH Chuẩn Hoàng Gia & Cổng Tra Cứu (Certificate & Verification)](#44-giấy-chứng-nhận-ctxh-chuẩn-hoàng-gia--cổng-tra-cứu-certificate--verification)
   - [4.5. Lịch Cá Nhân Thông Minh & Cảnh Báo Xung Đột (Smart Calendar)](#45-lịch-cá-nhân-thông-minh--cảnh-báo-xung-đột-smart-calendar)
   - [4.6. Trung Tâm Câu Lạc Bộ & Hợp Tác Đồng Tổ Chức (Groups & Co-hosting Hub)](#46-trung-tâm-câu-lạc-bộ--hợp-tác-đồng-tổ-chức-groups--co-hosting-hub)
   - [4.7. Trang Cá Nhân, Gamification & Bộ Sưu Tập Trophy (Profile & Trophies Showcase)](#47-trang-cá-nhân-gamification--bộ-sưu-tập-trophy-profile--trophies-showcase)
   - [4.8. Trợ Lý AI Sinh Viên (Smart Campus AI Floating Assistant)](#48-trợ-lý-ai-sinh-viên-smart-campus-ai-floating-assistant)
   - [4.9. Bảng Điều Khiển Quản Trị Hệ Thống (Admin Command Center)](#49-bảng-điều-khiển-quản-trị-hệ-thống-admin-command-center)
5. [MICRO-INTERACTIONS, CHUYỂN CẢNH & HIỆU ỨNG CẢM GIÁC (HAPTICS & ANIMATIONS)](#5-micro-interactions-chuyển-cảnh--hiệu-ứng-cảm-giác)

---

## 1. TRIẾT LÝ THIẾT KẾ & HỆ THỐNG THIẾT KẾ (DESIGN SYSTEM)

### 1.1. Triết lý: *"Vibrant Campus, Academic Prestige & Effortless Speed"*
- **Vibrant Campus (Năng động tuổi trẻ):** Không gian phong trào sinh viên cần năng lượng, màu sắc sống động, độ tương phản cao, thoát khỏi sự nhàm chán của các cổng thông tin đại học truyền thống.
- **Academic Prestige (Chuẩn mực & Danh giá):** Mọi chứng chỉ, huy hiệu Trophy, thông tin ngày CTXH phải toát lên sự trang trọng, uy tín, chính thống để sinh viên tự hào chia sẻ và nhà trường tin tưởng đối soát.
- **Effortless Speed (Tối giản thao tác - 1 chạm là xong):** Loại bỏ mọi thao tác thừa; điểm danh không cần xếp hàng, kiểm tra lịch không cần tính nhẩm.

---

### 1.2. Bảng màu chuẩn mực (Tailored Color Palette)
Hệ thống sử dụng không gian màu HSL chuẩn xác, đạt chuẩn tương phản tiếp cận **WCAG 2.1 AAA**:

```
Primary (Academic Navy / Royal Indigo): 
  - #1E3A8A (Deep Brand) | #3B82F6 (Action Accent) | #60A5FA (Focus Ring)
Secondary (Energetic Amber / Gold Prestige):
  - #F59E0B (CTXH Accent) | #D97706 (Trophy Gold) | #FEF3C7 (Badge Tint)
Cyber Emerald (Success / Check-in Active):
  - #10B981 (Success Emerald) | #059669 (Confirmed) | #D1FAE5 (Soft Green Pill)
Danger / Conflict (Alert Crimson):
  - #EF4444 (Conflict Alert) | #DC2626 (Deadline Urgent) | #FEE2E2 (Light Warning)
Neutrals & Dark Mode Surfaces:
  - Light Background: #F8FAFC (Slate 50) | Card: #FFFFFF | Border: #E2E8F0
  - Dark Background:  #0F172A (Slate 900) | Card: #1E293B | Border: #334155
```

---

### 1.3. Hệ thống Typography phân cấp mạnh mẽ
- **Font chính (Body & UI Components):** `Plus Jakarta Sans` hoặc `Inter` (Hình học hiện đại, hỗ trợ dấu tiếng Việt hoàn hảo, khoảng cách chữ thoáng).
- **Font tiêu đề danh giá (Headings & Trophy Titles):** `Outfit` hoặc `Syne` (Cá tính, sang trọng, mang hơi thở công nghệ cao).
- **Font mã chứng nhận & Chỉ số (Monospace Numbers):** `JetBrains Mono` (Dành cho mã `UC-XXXXXX`, tọa độ GPS, thời gian đếm ngược).

---

### 1.4. Chiều sâu thị giác & Hiệu ứng kính (Layered Glassmorphism)
- Sử dụng **3 tầng bóng đổ mềm (Soft Ambient Shadows)** thay vì viền đen cứng nhắc.
- **Backdrop-blur (Thủy tinh mờ cao cấp):**
  - Navigation Bar & Mobile Bottom Bar: `backdrop-filter: blur(16px); background: rgba(255, 255, 255, 0.82);`
  - Đảm bảo khi người dùng cuộn nội dung phía dưới, giao diện vẫn có chiều sâu mượt mà như iOS Native.

---

### 1.5. Quy chuẩn Biểu tượng Vector Thống nhất (Iconography System - Lucide Icons)
**Nguyên tắc bất di bất dịch:** Tuyệt đối không dùng Unicode Emoji hệ thống (vì emoji bị biến dạng khác nhau trên Windows, iOS, Android, macOS và không thể đồng bộ màu sắc theme).
Toàn bộ dự án chuẩn hóa 100% bằng bộ thư viện vector SVG **Lucide Icons** (`lucide-react`):
- **Đặc tính kỹ thuật:** Vector SVG sắc nét ở mọi độ phân giải, độ dày viền chuẩn `strokeWidth={1.75}`, thừa hưởng màu động `currentColor` theo CSS Tokens (Light/Dark Mode).
- **Quy chuẩn kích thước (Size Tokens):**
  - `icon-xs` (14px): Dùng cho huy hiệu nhỏ, metadata phụ, tag pill inline.
  - `icon-sm` (16px): Dùng cho nút bấm tiêu chuẩn, thông tin ngày giờ, địa điểm.
  - `icon-md` (20px): Dùng cho thanh điều hướng (Left Sidebar / Bottom Nav), nút CTA chính.
  - `icon-lg` (24px): Dùng cho tiêu đề mục, modal header, icon trung tâm FAB.
  - `icon-xl` (32px - 48px): Dùng cho huy hiệu Trophy, empty states, minh chứng thành tích.

#### Bảng ánh xạ Biểu tượng Chuẩn (Master Icon Mapping Table):
| Nhóm chức năng | Tên Icon Lucide | Mã Component JSX | Mục đích sử dụng |
| :--- | :--- | :--- | :--- |
| **Điều hướng chính** | `Compass` / `Flame` | `<Compass size={20} />` | Trang Khám phá / Bảng tin hoạt động |
| | `Calendar` | `<Calendar size={20} />` | Lịch cá nhân & Cảnh báo xung đột |
| | `Users` | `<Users size={20} />` | Câu lạc bộ & Cộng đồng sinh viên |
| | `Trophy` / `Award` | `<Trophy size={20} />` | Bộ sưu tập Trophy & Bảng thành tích |
| | `Bell` | `<Bell size={20} />` | Trung tâm thông báo & Cảnh báo điểm danh |
| | `Sparkles` / `Bot` | `<Sparkles size={20} />` | Trợ lý AI Sinh viên Thông minh |
| | `PlusCircle` / `Plus`| `<PlusCircle size={20} />` | Nút Tạo hoạt động mới |
| | `User` / `Settings` | `<User size={20} />` | Hồ sơ cá nhân & Cài đặt tài khoản |
| **Điểm danh & GPS** | `Radio` | `<Radio size={24} />` | Chế độ Radar Điểm danh 1-Chạm |
| | `QrCode` | `<QrCode size={24} />` | Chế độ Quét mã QR xoay 30s |
| | `MapPin` | `<MapPin size={16} />` | Tọa độ địa điểm & Bản đồ số |
| | `CheckCircle2` | `<CheckCircle2 size={16} />` | Xác nhận có mặt thành công |
| | `AlertTriangle` | `<AlertTriangle size={16} />` | Cảnh báo trùng lịch hoặc ngoài bán kính |
| **Minh chứng & CTXH**| `GraduationCap` | `<GraduationCap size={18} />`| Ngày Công tác Xã hội (CTXH) tốt nghiệp |
| | `FileCheck` | `<FileCheck size={18} />` | Giấy chứng nhận tham gia hợp lệ |
| | `Download` / `Printer`| `<Printer size={16} />` | In / Tải PDF chứng nhận A4 Landscape |
| | `ShieldCheck` | `<ShieldCheck size={16} />` | Tích xanh Tổ chức uy tín (Verified Org) |
| | `Handshake` | `<Handshake size={16} />` | Huy hiệu Hoạt động Đồng tổ chức liên CLB |
| **Tương tác & Xã hội**| `Heart` | `<Heart size={16} />` | Nút Thích sự kiện |
| | `MessageSquare` | `<MessageSquare size={16} />`| Bình luận & Thảo luận |
| | `Bookmark` | `<Bookmark size={16} />` | Lưu trữ hoạt động quan tâm |
| | `Share2` | `<Share2 size={16} />` | Chia sẻ sự kiện |
| | `Search` | `<Search size={16} />` | Thanh tìm kiếm toàn cục (Ctrl + K) |

---

## 2. PHÂN KHÚC NGƯỜI DÙNG & CHIẾN LƯỢC THIẾT KẾ THÍCH ỨNG

Thiết kế giao diện phải thông minh biến hóa tùy theo mức độ thuần thục của từng nhóm người dùng:

| Nhóm đối tượng | Tâm lý & Nhu cầu cốt lõi | Chiến lược thiết kế UI/UX |
| :--- | :--- | :--- |
| **New User** *(Sinh viên năm nhất / Người mới đăng ký)* | • Bỡ ngỡ, chưa biết ngày CTXH là gì.<br>• Sợ thao tác sai, ngại điền form dài.<br>• Muốn tìm bạn bè, CLB hợp sở thích. | • **Onboarding 3 bước nhẹ nhàng:** Chọn khoa, trường, sở thích (Pills selector).<br>• **Micro-copy thân thiện:** Giải thích ngắn gọn *"1 ngày CTXH = 8 giờ tình nguyện tích lũy tốt nghiệp"* bằng Tooltip thông minh.<br>• **Empty state truyền cảm hứng:** *"Chưa có sự kiện nào? Khám phá ngay 5 hoạt động 'hot' dành riêng cho K65!"*. |
| **Active Core User** *(Sinh viên năng nổ / Săn ngày CTXH)* | • Cần tốc độ cao.<br>• Theo dõi tiến độ tích lũy CTXH & Trophy.<br>• Sợ trùng lịch thi, lịch học. | • **Thẻ sự kiện giàu dữ liệu (Data-rich cards):** Nhìn thấy ngay số ngày CTXH, hạn chót, khoảng cách GPS.<br>• **1-Chạm điểm danh (Radar Prompt):** Nhận notification là xác nhận ngay.<br>• **Cảnh báo xung đột lịch trực quan:** Huy hiệu vàng cảnh báo ngay trên nút Đăng ký. |
| **Super User / Organizer** *(Chủ nhiệm CLB, Bí thư Đoàn khoa)* | • Áp lực điều phối hàng trăm thành viên.<br>• Cần điểm danh nhanh không nghẽn.<br>• Quản lý form đăng ký, mời CLB khác đồng tổ chức. | • **Host Command Bar:** Thanh điều khiển nổi ở đầu màn hình sự kiện.<br>• **Màn hình Radar thời gian thực:** Nhìn thấy số lượng người có mặt nhảy số trực tiếp.<br>• **Bulk Actions:** Duyệt hàng loạt người tham gia, xuất Excel chỉ với 1 click. |
| **Authority / Admin** *(Phòng CTSV, Quản trị viên trường)* | • Cần tính chính xác, minh bạch tuyệt đối.<br>• Thao tác trên tập dữ liệu lớn.<br>• Tra cứu đối soát nhanh chóng. | • **Mật độ thông tin cao (High density tables):** Bộ lọc đa chiều (Khoa, MSSV, Khóa).<br>• **Drawer xem nhanh (Quick Inspection Drawer):** Bấm xem chứng nhận mà không cần rời trang.<br>• **1-Click Audit & Export:** Đối soát dữ liệu cấp trường chỉ bằng một báo cáo chuẩn. |

---

## 3. KIẾN TRÚC GIAO DIỆN ĐA NỀN TẢNG (DESKTOP WEB VS. MOBILE APP NATIVE)

### 3.1. Desktop Web (Màn hình rộng $\ge$ 1024px) - Kiến trúc Left Sidebar / Tri-Pane Layout Hiện Đại
Tuân thủ xu hướng thiết kế hàng đầu của các nền tảng thế hệ mới (**Threads, Instagram Web, X, Linear, Notion, Discord**): Loại bỏ hoàn toàn Top Navigation truyền thống để chuyển sang **Left Navigation Bar (Sidebar / Navigation Rail)** kết hợp bố cục 3 cột (Tri-Pane Layout).

#### Lợi ích vượt trội:
1. **Giải phóng chiều dọc màn hình:** Tận dụng không gian chiều ngang vô tận của màn hình Widescreen (16:9, 21:9), giúp khu vực cuộn bảng tin và lịch rộng rãi, thoáng đãng hơn 35%.
2. **Nhất quán với Mobile App:** Đồng bộ hoàn hảo giữa *Thanh điều hướng dưới đáy (Bottom Nav)* trên điện thoại và *Thanh điều hướng cạnh trái (Left Nav Rail)* trên máy tính.
3. **Chế độ Co giãn Linh hoạt (Responsive Rail):**
   - Màn hình 13-14 inch (1024px - 1440px): Tự thu nhỏ thành **Navigation Rail (72px)** dạng Icon tinh gọn với Tooltip nổi (chuẩn Threads/Instagram).
   - Màn hình lớn ($\ge$ 1440px): Mở rộng thành **Full Sidebar (250px)** với đầy đủ Tên nhãn, Badge đếm thông báo, Nút tạo hoạt động to bản và Thẻ Profile cá nhân ở chân trang.

#### Sơ đồ Bố cục 3 Cột (Tri-Pane Desktop Layout) với Icon Lucide:
```
+-------------------+-----------------------------------------+-------------------------------+
| CỘT 1: SIDEBAR    | CỘT 2: KHÔNG GIAN CHÍNH (FEED / DETAIL) | CỘT 3: TIỆN ÍCH (WIDGETS)     |
| (250px cố định)   | (640px - 720px trung tâm)               | (320px bên phải)              |
+-------------------+-----------------------------------------+-------------------------------+
| [UniConnect Logo] | [ <Search /> Tìm sự kiện, CLB... Ctrl+K]| <GraduationCap /> TIẾN ĐỘ CTXH|
| (Phát sáng nhẹ)   |                                         | • Đã đạt: 4.5 / 5.0 ngày      |
|                   | BỘ LỌC CHIPS: [Tất cả] [Hot] [Có CTXH]  | • [██████████░] 90% tốt nghiệp|
| <Compass />       |                                         |                               |
|   Khám phá        | +-------------------------------------+ | <Calendar /> LỊCH TRONG TUẦN  |
| <Calendar />      | | THẺ HOẠT ĐỘNG MASTER                | | • 14:00 Hôm nay: Tech Talk  |
|   Lịch của tôi    | | <Handshake /> CLB IT x CLB Anh văn  | | • 07:30 T7: Chủ Nhật Xanh   |
| <Users />         | | Tech Hackathon 2026                 | |                               |
|   Câu lạc bộ      | | <Award /> 1.0 CTXH  <Trophy /> IT   | <MapPin /> BẢN ĐỒ XUNG QUANH  |
| <Trophy />        | | [<CheckCircle2 /> Đăng ký - 1 chạm] | [Ghim Hội trường A, Sân bóng] |
|   Trophy của tôi  | +-------------------------------------+ |                               |
| <Bell />          |                                         | <Users /> CLB ĐỀ XUẤT CHO BẠN |
|   Thông báo [3]   | +-------------------------------------+ | [Logo] CLB Nhiếp ảnh [Join]   |
| <Sparkles />      | | THẺ HOẠT ĐỘNG TIẾP THEO             | | [Logo] CLB Âm nhạc   [Join]   |
|   Trợ lý AI Uni   | | ...                                 | |                               |
|                   | +-------------------------------------+ |                               |
| [<PlusCircle />   |                                         |                               |
|  TẠO HOẠT ĐỘNG]   |                                         |                               |
| ----------------- |                                         |                               |
| [Avatar] Tuấn Anh |                                         |                               |
| MSSV: 22001234    |                                         |                               |
| [<Settings />]    |                                         |                               |
+-------------------+-----------------------------------------+-------------------------------+
```

---

### 3.2. Mobile Web & App Native Feel (Màn hình di động $\le$ 768px)
- **Thiết kế chuẩn ngón tay cái (Thumb-Zone Navigation):** Toàn bộ thao tác chính nằm ở nửa dưới màn hình để người dùng sử dụng một tay thoải mái.
- **Bottom Navigation Bar (Thanh điều hướng 5 vị trí cao cấp với Lucide SVG Icons):**
  1. `<Compass size={22} />` **Khám phá (Feed):** Trang chủ hoạt động phong trào.
  2. `<Calendar size={22} />` **Lịch của tôi (Calendar):** Quản lý lịch trình & cảnh báo trùng giờ.
  3. `<Radio size={24} />` / `<Plus size={24} />` **Nút trung tâm nổi (Floating Action Button - FAB):** Nút tròn phát sáng chuyển đổi linh hoạt:
     - Nếu đang có sự kiện diễn ra: **"Xác nhận có mặt (Radar GPS)"**.
     - Nếu là Host/BCN: **"Tạo hoạt động mới"**.
  4. `<Users size={22} />` **Cộng đồng (CLB):** Các nhóm và hoạt động liên CLB.
  5. `<User size={22} />` **Cá nhân (Profile):** Bộ sưu tập Trophy & Minh chứng CTXH.
- **Bottom Sheet Drawer:** Mọi popup điền form, chọn bộ lọc hoặc quét vị trí đều trượt từ dưới lên (Swipeable bottom sheet), hỗ trợ thao tác vuốt xuống để đóng mượt mà như app native iOS/Android.

```
+-----------------------------------+
| [UniConnect]  <Search />  <Bell />|  <- Header mỏng
+-----------------------------------+
|  Story / Highlights CLB           |
|  (Avatar tròn có viền gradient)   |
+-----------------------------------+
|  THẺ SỰ KIỆN NỔI BẬT              |
|  +-----------------------------+  |
|  | [Ảnh bìa sắc nét]           |  |
|  | <Handshake /> CLB IT x Anh văn |  |
|  | Tech Hackathon 2026         |  |
|  | <Award /> 1.0 CTXH  <Trophy /> |  |
|  | [<CheckCircle2 /> Đăng ký]  |  |
|  +-----------------------------+  |
+-----------------------------------+
| [<Compass>] [<Calendar>] [( <Radio> )] [<Users>] [<User>] |  <- Bottom Nav chuẩn Native App
+-----------------------------------+
```

---

## 4. ĐẶC TẢ CHI TIẾT TỪNG MÀN HÌNH CỐT LÕI (PAGE-BY-PAGE SPECS)

### 4.1. Trang Chủ / Khám Phá Sự Kiện (Discovery & Dashboard)

#### Trải nghiệm cho New User:
- **Banner chào đón cá nhân hóa:** *"Chào Tân sinh viên [Tên]! Bắt đầu tích lũy ngày CTXH đầu tiên của bạn nào!"*.
- **Quick Onboarding Pill Filter:** Gợi ý sẵn các tag: `#Dành_cho_K65`, `#Học_thuật`, `#Tình_nguyện_xanh`, `#Workshop_kỹ_năng`.

#### Trải nghiệm cho Core & Super User:
- **Widget đếm ngược sự kiện sắp tới (Upcoming Event Countdown):** Thẻ thông minh hiển thị sự kiện gần nhất mà người dùng đã đăng ký kèm đồng hồ đếm ngược và chỉ dẫn đường đi.
- **Thẻ Hoạt Động Cực Kỳ Sang Trọng (Master Activity Card):**
  - **Header thẻ:** Avatar CLB chủ trì 🤝 Avatar CLB đồng tổ chức + Tên các đơn vị + Huy hiệu xác minh tích xanh.
  - **Cover Image:** Tỷ lệ 16:9 sắc nét, phủ gradient tối nhẹ ở chân ảnh để tôn chữ.
  - **Huy hiệu nổi bật trên ảnh:**
    - Huy hiệu CTXH: Màu hổ phách sang trọng `🌱 1.0 Ngày CTXH`.
    - Huy hiệu Trophy: Màu vàng kim óng ánh `🏆 Cúp Công nghệ`.
    - Huy hiệu Thời gian: `⏰ Còn 2 ngày đóng đơn`.
  - **Chân thẻ:** Số lượng người tham gia dạng thanh tiến trình (Progress bar: *45/50 chỗ*) + Nút tương tác nhanh (Thích, Chia sẻ, Bookmark).

---

### 4.2. Trang Chi Tiết Hoạt Động & Đăng Ký (Activity Detail & Dynamic Form)

#### Bố cục & Phân cấp thị giác:
1. **Hero Header Parallax:** Ảnh bìa lớn, tự thu gọn mượt mà khi cuộn trang.
2. **Khung Nhận Diện Tổ Chức Liên Danh (Co-host Showcase Bar):**
   - Hộp kính thủy tinh mờ viền sáng nổi bật:  
     `Được phối hợp tổ chức bởi: [Logo CLB A] CLB Tin học  🤝  [Logo CLB B] CLB Tiếng Anh`.
   - Nút *"Theo dõi CLB"* nằm ngay bên cạnh giúp sinh viên tiện kết nối.
3. **Thanh Thông Số Vàng (Quick Stat Pills):** 4 thẻ chỉ số nhanh:
   - 📅 **Thời gian:** 08:00 - 11:30 | 20/09/2026
   - 📍 **Địa điểm:** Hội trường A2 (Kèm link mở bản đồ chỉ đường)
   - 🌱 **Công tác xã hội:** 1.0 Ngày chính thức
   - 🏆 **Huy hiệu danh dự:** Trophy "Hiệp sĩ IT" (+50 điểm)
4. **Khu vực Đăng ký & Biểu mẫu tùy biến (Dynamic Form Experience):**
   - Nút **"Đăng ký tham gia"** ghim cố định ở đáy màn hình di động (Sticky Bottom CTA).
   - Nếu có biểu mẫu: Bấm nút sẽ mở **Bottom Sheet / Modal mượt mà** với các trường câu hỏi được nhóm rõ ràng, có thanh tiến trình `Bước 1/2`.
   - Hỗ trợ kéo-thả tải tệp minh chứng (Drag-and-drop file upload) có preview ảnh ngay lập tức.
5. **Thanh Điều Khiển Cho Host (Organizer Floating Action Bar):**
   - Nếu người xem là Ban tổ chức (Host hoặc BCN CLB đồng tổ chức), đáy trang sẽ hiện thanh điều khiển chuyên dụng:
     - `[📍 Mở Radar Điểm danh]`
     - `[👥 Quản lý danh sách (50)]`
     - `[📊 Xuất báo cáo]`

---

### 4.3. Trải Nghiệm Điểm Danh Radar GPS 1-Chạm (Proximity Radar Attendance UX)

Đây là tính năng đột phá nhất về mặt UX của UniConnect, loại bỏ hoàn toàn phiền toái của việc quét mã QR.

#### Góc nhìn của Ban Tổ Chức (Host Radar Screen):
- Host bấm **"Mở phiên điểm danh"** $\rightarrow$ Chọn thời gian (mặc định 3 phút) $\rightarrow$ Bấm **"Bắt đầu phát sóng"**.
- Màn hình chuyển sang giao diện **Radar Radar Scanner** cực kỳ công nghệ cao:
  - Vòng tròn sóng radar lan tỏa tỏa ra từ tâm (Hiệu ứng Ripple Animation).
  - Vòng tròn hiển thị bán kính an toàn (100m).
  - Khi sinh viên bấm điểm danh, các chấm xanh đại diện cho sinh viên xuất hiện kèm avatar bay vào tâm:
    - *🟢 Nguyễn Văn A (Cách 8m)*
    - *🟢 Trần Thị B (Cách 15m)*
  - Bộ đếm thời gian đếm ngược dạng số điện tử lớn: `02:45` và bộ đếm sĩ số: `Đã có mặt: 42 / 50 bạn`.
  - Nút khẩn cấp: `[Duyệt thủ công]` hoặc `[Đóng phiên sớm]`.

#### Góc nhìn của Sinh viên (Student 1-Tap Experience):
- Sinh viên nhận thông báo đẩy / rung chuông trên điện thoại:  
  *“🔔 Điểm danh hoạt động [Tech Hackathon] đã mở! Bạn có 3 phút để xác nhận.”*
- Chạm vào thông báo $\rightarrow$ Ứng dụng tự mở ngay **Popup 1-Chạm Siêu Lớn**:
  - Tiêu đề: `📍 Xác nhận bạn đang có mặt tại sự kiện`
  - Vòng tròn định vị hiển thị khoảng cách ước tính: `Bạn đang ở cách Ban tổ chức 12 mét (Hợp lệ)`.
  - Một nút bấm tròn lớn to bản chiếm 50% màn hình, hiệu ứng sóng nước phát sáng:  
    👉 **[ TÔI ĐÃ CÓ MẶT ]** 👈
  - Sinh viên chạm ngón tay vào nút: Điện thoại phản hồi rung nhẹ (Haptic feedback) $\rightarrow$ Vòng tròn đổi sang **Tích xanh thành công** kèm âm thanh "Ting!" sang trọng $\rightarrow$ Màn hình tung hoa giấy (Confetti Animation) chúc mừng bạn đã nhận được **1.0 Ngày CTXH** và **Huy hiệu Trophy**.

---

### 4.4. Giấy Chứng Nhận CTXH Chuẩn Hoàng Gia & Cổng Tra Cứu (Certificate & Verification)

#### Thiết kế Giấy chứng nhận (Certificate Modal & Print A4 Landscape):
- **Phong cách:** Sang trọng chuẩn văn bằng đại học kết hợp công nghệ hiện đại.
- **Họa tiết viền hoa văn (Guilloche Border):** Khung viền hoa văn cổ điển màu xanh Navy ánh vàng kim.
- **Tiêu đề & Quốc hiệu:** Trình bày trang nghiêm với font chữ có chân uy nghi.
- **Tên đơn vị tổ chức:** Tự động ghi nhận đầy đủ liên danh các đơn vị:  
  *“Đoàn khoa Công nghệ Thông tin phối hợp cùng CLB Tin học & CLB Tiếng Anh”*.
- **Dấu mộc bảo chứng điện tử (Digital Verified Seal):** Con dấu đỏ bo tròn có logo UniConnect phát sáng ánh kim chìm dưới chữ ký.
- **Mã QR Tra Cứu & Mã Định Danh:** Đặt trang trọng ở góc dưới bên trái cùng mã `UC-A8F31C-9D4E21`.
- **Hành động 1-Click:** Nút **"Tải PDF / In ấn"** tự động kích hoạt chế độ in ấn A4 chuẩn tỉ lệ vàng, loại bỏ hoàn toàn viền thừa của trình duyệt.

#### Cổng Tra Cứu Trực Tuyến (/verify-certificate):
- Giao diện siêu tối giản, tập trung vào sự tin cậy tuyệt đối:
  - Thẻ xác minh màu xanh ngọc (Emerald Card) nổi bật: **“CHỨNG NHẬN ĐÃ ĐỐI SOÁT CHÍNH THỨC TỪ HỆ THỐNG UNICONNECT”**.
  - Liệt kê minh bạch: Tên sinh viên, MSSV, Sự kiện, Số ngày CTXH được ghi nhận, Ngày giờ điểm danh chính xác từng giây.
  - Phù hợp hoàn hảo cho màn hình điện thoại của cán bộ Phòng CTSV khi dùng camera quét kiểm tra.

---

### 4.5. Lịch Cá Nhân Thông Minh & Cảnh Báo Xung Đột (Smart Calendar)

- **Các chế độ xem:** Chuyển đổi linh hoạt Tháng / Tuần / Ngày / Agenda bằng thanh trượt Segmented Control.
- **Hệ thống phân màu sự kiện thông minh:**
  - 🔵 Màu Xanh dương: Hoạt động UniConnect đã đăng ký.
  - 🟣 Màu Tím: Lịch cá nhân tự thêm (Lịch học, lịch thi, việc bận).
  - 🟢 Màu Xanh lá: Sự kiện đã đồng bộ từ Google Calendar.
- **Trải nghiệm Cảnh Báo Xung Đột Thời Gian (Conflict Resolver UI):**
  - Nếu sinh viên chuẩn bị đăng ký một sự kiện bị trùng giờ với lịch có sẵn:
  - Nút đăng ký sẽ đổi sang trạng thái màu hổ phách: `⚠️ Trùng lịch! Bấm để xem chi tiết`.
  - Bấm vào sẽ mở thẻ so sánh trực quan giữa 2 sự kiện kèm thời gian giao thoa và câu hỏi:  
    *"Bạn có chắc chắn muốn tiếp tục đăng ký sự kiện này không?"*.

---

### 4.6. Trung Tâm Câu Lạc Bộ & Hợp Tác Đồng Tổ Chức (Groups & Co-hosting Hub)

- **Trang chi tiết CLB (Club Showcase):**
  - Ảnh bìa tràn viền (Cover banner) + Logo tròn đè lên góc trái + Huy hiệu `Verified Organization` tích xanh.
  - Thống kê thành tích CLB: *1,200 Thành viên | 24 Sự kiện đã tổ chức | 450 Ngày CTXH đã đóng góp cho cộng đồng*.
- **Hộp Thư Lời Mời Phối Hợp Đồng Tổ Chức (Co-host Inbox dành cho BCN):**
  - Một tab riêng biệt chỉ hiển thị cho Ban chủ nhiệm CLB.
  - Thẻ lời mời:  
    `[Logo CLB Tin học] CLB Tin học mời bạn đồng tổ chức sự kiện "Hackathon K65"`.
    - Xem chi tiết phân chia công việc & quyền hạn điểm danh.
    - 2 nút hành động nhanh: **`[✅ Chấp nhận]`** và **`[❌ Từ chối]`** kèm phản hồi tin nhắn.

---

### 4.7. Trang Cá Nhân, Gamification & Bộ Sưu Tập Trophy (Profile & Trophies Showcase)

- **Thẻ Hộ Chiếu Sinh Viên (Student Passport Card):**
  - Thiết kế dạng thẻ card ngân hàng bo góc sang trọng, phủ gradient tím than ánh kim.
  - Hiển thị: Họ tên, MSSV, Trường/Khoa và 3 con số tự hào:
    - 🌟 **Số hoạt động hoàn thành**
    - 🌱 **Tổng số ngày CTXH đã tích lũy** (kèm thanh tiến trình mục tiêu tốt nghiệp: *4.5 / 5.0 ngày*)
    - 🏆 **Tổng số Trophy thu hoạch được**
- **Bộ Sưu Tập Trophy 3D (Trophy Showcase Grid):**
  - Các huy hiệu Trophy hiển thị dạng lưới với hiệu ứng chiếu sáng 3D nhẹ.
  - Trophy đã đạt: Sáng rõ rực rỡ, bấm vào sẽ xoay 360 độ và hiển thị ngày đạt được cùng tên sự kiện.
  - Trophy chưa đạt: Hiển thị bóng mờ (Locked state) kèm gợi ý: *"Tham gia sự kiện Ngày Chủ Nhật Xanh để mở khóa huy hiệu này"*.

---

### 4.8. Trợ Lý AI Sinh Viên (Smart Campus AI Floating Assistant)

- **Vị trí hiển thị:** 
  - Nút tròn trợ lý AI phát sáng dạng quả cầu năng lượng (Gradient Orb) nổi ở góc dưới bên phải màn hình (Desktop & Mobile).
- **Trải nghiệm tương tác:**
  - Chạm vào nút mở ra cửa sổ Chat dạng Bottom Sheet (trên di động) hoặc Cửa sổ nổi Glassmorphism (trên máy tính).
  - Gợi ý sẵn 3 câu hỏi nhanh (Prompt chips):
    - *"Cuối tuần này có hoạt động CTXH nào không?"*
    - *"Kiểm tra xem lịch thứ 7 của mình có trống không?"*
    - *"CLB nào đang tuyển thành viên mới?"*
  - Câu trả lời của AI không chỉ là văn bản khô khan mà trả về trực tiếp **Thẻ Sự Kiện Tương Tác** (Interactive Event Card) có nút bấm đăng ký ngay trong luồng chat.

---

### 4.9. Bảng Điều Khiển Quản Trị Hệ Thống (Admin Command Center)

- **Phong cách:** Mật độ thông tin cao, sắc nét, trực quan, phục vụ kiểm soát toàn trường trong 1 màn hình:
  - **Hàng chỉ số KPI đỉnh cao (Metrics Row):** 4 thẻ widget hiển thị số liệu kèm biểu đồ mini (Sparklines) và tỷ lệ tăng trưởng so với tháng trước (+18.4%).
  - **Hàng đợi Phê duyệt Tích xanh (Verified Org Approvals):** Danh sách các CLB nộp đơn xin xác minh kèm nút xem nhanh hồ sơ pháp lý và nút Duyệt / Từ chối tức thì.
  - **Bảng Tra cứu & Kiểm toán Sinh viên (Master Student Audit Table):** Tìm kiếm theo MSSV, xem toàn bộ lịch sử tham gia và ngày CTXH, hỗ trợ xuất báo cáo Excel cho toàn trường trong 1 giây.

---

## 5. MICRO-INTERACTIONS, CHUYỂN CẢNH & HIỆU ỨNG CẢM GIÁC

Để biến UniConnect thành một ứng dụng đạt tiêu chuẩn giải thưởng thiết kế (Awwwards / Apple Design Award):

1. **Hiệu ứng xúc giác (Haptic Feedback trên điện thoại):**
   - Rung nhẹ (Light impact) khi bấm nút tab chuyển trang hoặc nút Thích.
   - Rung xác nhận thành công (Success notification haptic) khi bấm điểm danh GPS 1-chạm thành công.
2. **Skeleton Shimmer Loading:**
   - Tuyệt đối không dùng vòng quay Loading Spinner đơn điệu.
   - Sử dụng khung xương màu xám nhạt quét sóng ánh sáng (Shimmer) đúng theo kích thước của thẻ sự kiện và profile trong lúc chờ tải dữ liệu.
3. **Hiệu ứng Chúc mừng (Confetti Celebration):**
   - Khi hoàn thành điểm danh hoặc mở khóa Trophy mới, hiệu ứng pháo hoa giấy mini bung nhẹ trên màn hình mang lại cảm giác thành tựu và khích lệ sinh viên.
4. **Chuyển cảnh mượt mà 60fps (Smooth Transitions):**
   - Mọi thao tác mở modal, đóng drawer đều áp dụng đường cong chuyển động tự nhiên (`cubic-bezier(0.16, 1, 0.3, 1)` - Spring physics).

---
*Bản đặc tả thiết kế UI/UX được hoàn thiện và sẵn sàng để đội ngũ Kỹ thuật viên & Frontend Developers hiện thực hóa vào mã nguồn UniConnect.*
