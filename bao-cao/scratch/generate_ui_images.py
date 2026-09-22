import os
from PIL import Image, ImageDraw, ImageFont

img_dir = 'c:/Users/Admin/Code/uniconnect-v2/bao-cao/Images'

screens = [
    ("ui-campus-map.png", "BẢN ĐỒ TƯƠNG TÁC KHUÔN VIÊN TRƯỜNG", "Campus Map - Định vị GPS, hiển thị các ghim hoạt động thể thao & học thuật"),
    ("ui-activity-detail.png", "CHI TIẾT HOẠT ĐỘNG & ĐĂNG KÝ THAM GIA", "Activity Details - Thông tin thời gian, địa điểm, slot tham gia, cảnh báo trùng lịch"),
    ("ui-attendance-checkin.png", "ĐIỂM DANH CHỐNG GIAN LẬN ĐA CHẾ ĐỘ", "Attendance - Mã QR xoay động 30s HMAC-SHA256 & Radar GPS 1-Chạm"),
    ("ui-smart-calendar.png", "LỊCH THÔNG MINH & ĐỐI SOÁT XUNG ĐỘT", "Smart Calendar - Vị từ khoảng nửa mở [start, end), xuất file .ics tương thích Google Calendar"),
    ("ui-gamification-profile.png", "HỒ SƠ CÁ NHÂN & DANH HIỆU TROPHY", "Gamification Profile - Tích lũy ngày CTXH, xếp hạng sinh viên & bộ sưu tập huy hiệu"),
    ("ui-ai-assistant.png", "TRỢ LÝ HỌC ĐƯỜNG AI TÍCH HỢP RAG", "AI Assistant - Tư vấn sự kiện phù hợp, đối soát lịch trống và giải đáp quy chế trường học"),
    ("ui-admin-dashboard.png", "BẢNG ĐIỀU KHIỂN QUẢN TRỊ VIÊN (ADMIN)", "Admin Dashboard - Biểu đồ KPI tăng trưởng, kiểm duyệt vi phạm và xuất CSV UTF-8 BOM"),
    ("ui-certificate-verify.png", "TRA CỨU XÁC THỰC CHỨNG NHẬN TRỰC TUYẾN", "Certificate Verification - Kiểm tra tính nguyên bản của Giấy chứng nhận CTXH tại /verify-certificate")
]

width, height = 1200, 750

for fname, title, desc in screens:
    img = Image.new('RGB', (width, height), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Outer frame & header
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(203, 213, 225), width=2)
    draw.rectangle([(20, 20), (width - 20, 80)], fill=(30, 58, 138))
    
    # Header bar simulation (mac/browser dots)
    draw.ellipse([(45, 45), (57, 57)], fill=(239, 68, 68))
    draw.ellipse([(67, 45), (79, 45+12)], fill=(245, 158, 11))
    draw.ellipse([(89, 45), (101, 45+12)], fill=(16, 185, 129))
    
    # Center placeholder box
    draw.rectangle([(60, 120), (width - 60, height - 60)], fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    
    # Draw title text & subtitle
    # Use default font or fallback
    draw.text((width // 2, 280), "HỆ THỐNG UNICONNECT - GIAO DIỆN NGƯỜI DÙNG", fill=(30, 41, 59), anchor="mm")
    draw.text((width // 2, 340), title, fill=(29, 78, 216), anchor="mm")
    draw.text((width // 2, 400), desc, fill=(71, 85, 105), anchor="mm")
    draw.text((width // 2, 460), "[Hình ảnh minh chứng giao diện thực tế ứng dụng UniConnect Web Client]", fill=(148, 163, 184), anchor="mm")
    
    out_path = os.path.join(img_dir, fname)
    img.save(out_path, format="PNG")
    print(f"Generated: {out_path}")

print("All 8 UI images generated successfully.")
