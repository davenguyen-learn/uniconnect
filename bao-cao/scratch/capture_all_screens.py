import os
import sys
import time
import json
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

img_dir = r"c:\Users\Admin\Code\uniconnect-v2\bao-cao\Images"
os.makedirs(img_dir, exist_ok=True)

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1440,900")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

print("Khởi chạy Chrome headless chụp chuẩn 8 màn hình...")
driver = webdriver.Chrome(options=options)

def login(email, pwd):
    driver.get("http://localhost:5173/login")
    time.sleep(1.0)
    driver.execute_script("localStorage.clear();")
    driver.refresh()
    time.sleep(1.5)
    
    email_el = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
    )
    email_el.clear()
    email_el.send_keys(email)
    pwd_el = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
    pwd_el.clear()
    pwd_el.send_keys(pwd)
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    time.sleep(2.5)

sample_act_id = "5216ddf9-7249-47dc-9860-0c82647c1711"
cert_code = "UC-5216DD-8C4A2B"

try:
    # ── MÀN HÌNH 1: Dashboard & Bản đồ Campus ──
    print("\n[1/8] Đang chụp: ui-campus-map.png (Dashboard & Campus Map)...")
    login("dat.nguyen@hcmut.edu.vn", "dat123")
    driver.get("http://localhost:5173/dashboard")
    time.sleep(3.5)
    p1 = os.path.join(img_dir, "ui-campus-map.png")
    driver.save_screenshot(p1)
    print(f"   ✓ Đã lưu: {p1} ({os.path.getsize(p1)} bytes)")

    # ── MÀN HÌNH 2: Chi tiết Hoạt động ──
    print("\n[2/8] Đang chụp: ui-activity-detail.png (Activity Details)...")
    driver.get(f"http://localhost:5173/activities/{sample_act_id}")
    time.sleep(3.5)
    p2 = os.path.join(img_dir, "ui-activity-detail.png")
    driver.save_screenshot(p2)
    print(f"   ✓ Đã lưu: {p2} ({os.path.getsize(p2)} bytes)")

    # ── MÀN HÌNH 3: Điểm danh Đa chế độ (QR HMAC xoay 30s) ──
    print("\n[3/8] Đang chụp: ui-attendance-checkin.png (Mã QR Điểm danh xoay 30s)...")
    try:
        qr_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Hiển thị QR') or contains(., 'QR Điểm danh')]"))
        )
        qr_btn.click()
        time.sleep(2.0)
    except Exception as e:
        print(f"   (Không tìm thấy nút QR: {e})")
    p3 = os.path.join(img_dir, "ui-attendance-checkin.png")
    driver.save_screenshot(p3)
    print(f"   ✓ Đã lưu: {p3} ({os.path.getsize(p3)} bytes)")

    # ── MÀN HÌNH 4: Lịch Thông minh ──
    print("\n[4/8] Đang chụp: ui-smart-calendar.png (Smart Calendar)...")
    driver.get("http://localhost:5173/calendar")
    time.sleep(3.0)
    p4 = os.path.join(img_dir, "ui-smart-calendar.png")
    driver.save_screenshot(p4)
    print(f"   ✓ Đã lưu: {p4} ({os.path.getsize(p4)} bytes)")

    # ── MÀN HÌNH 5: Hồ sơ Cá nhân & Gamification ──
    print("\n[5/8] Đang chụp: ui-gamification-profile.png (Profile & CTXH)...")
    driver.get("http://localhost:5173/profile")
    time.sleep(3.0)
    p5 = os.path.join(img_dir, "ui-gamification-profile.png")
    driver.save_screenshot(p5)
    print(f"   ✓ Đã lưu: {p5} ({os.path.getsize(p5)} bytes)")

    # ── MÀN HÌNH 6: Trợ lý Học đường AI RAG ──
    print("\n[6/8] Đang chụp: ui-ai-assistant.png (AI Assistant with Cards)...")
    driver.get("http://localhost:5173/chat")
    time.sleep(2.0)
    try:
        chips = driver.find_elements(By.CSS_SELECTOR, "button.chat-prompt-chip")
        if chips:
            print(f"   -> Click chip gợi ý: '{chips[0].text}'...")
            chips[0].click()
            time.sleep(6.5)
    except Exception as e:
        print(f"   (Lỗi click chip: {e})")
    p6 = os.path.join(img_dir, "ui-ai-assistant.png")
    driver.save_screenshot(p6)
    print(f"   ✓ Đã lưu: {p6} ({os.path.getsize(p6)} bytes)")

    # ── MÀN HÌNH 7: Bảng điều khiển Quản trị viên ──
    print("\n[7/8] Đang chụp: ui-admin-dashboard.png (Admin Control Center)...")
    login("admin@hcmut.edu.vn", "admin123")
    driver.get("http://localhost:5173/admin")
    time.sleep(3.5)
    p7 = os.path.join(img_dir, "ui-admin-dashboard.png")
    driver.save_screenshot(p7)
    print(f"   ✓ Đã lưu: {p7} ({os.path.getsize(p7)} bytes)")

    # ── MÀN HÌNH 8: Tra cứu Xác thực Chứng nhận ──
    print("\n[8/8] Đang chụp: ui-certificate-verify.png (Certificate Verification Portal)...")
    driver.get(f"http://localhost:5173/verify-certificate?code={cert_code}")
    time.sleep(3.0)
    p8 = os.path.join(img_dir, "ui-certificate-verify.png")
    driver.save_screenshot(p8)
    print(f"   ✓ Đã lưu: {p8} ({os.path.getsize(p8)} bytes)")

    print("\n✨ HOÀN THÀNH XUẤT SẮC 8/8 ẢNH GIAO DIỆN THỰC TẾ CHO LUẬN VĂN!")

finally:
    driver.quit()
