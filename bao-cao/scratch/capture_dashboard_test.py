import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

out_dir = r"c:\Users\Admin\Code\uniconnect-v2\bao-cao\scratch"
screenshot_path = os.path.join(out_dir, "test_dashboard_shot.png")

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1440,900")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

print("Khởi chạy Chrome headless...")
driver = webdriver.Chrome(options=options)

try:
    # 1. Truy cập login
    print("Truy cập http://localhost:5173/login...")
    driver.get("http://localhost:5173/login")
    time.sleep(2)

    # 2. Đăng nhập
    email_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='email']"))
    )
    email_input.clear()
    email_input.send_keys("dat.nguyen@hcmut.edu.vn")

    pwd_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
    pwd_input.clear()
    pwd_input.send_keys("dat123")

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()
    print("Đã gửi form đăng nhập...")

    # 3. Đợi chuyển hướng sang dashboard
    time.sleep(3)
    current_url = driver.current_url
    print("URL hiện tại:", current_url)

    if "/dashboard" not in current_url:
        driver.get("http://localhost:5173/dashboard")
        time.sleep(3)

    # 4. Đợi bản đồ và card hoạt động xuất hiện
    print("Đợi các phần tử dashboard nạp xong...")
    time.sleep(3)

    # Lưu ảnh chụp màn hình
    driver.save_screenshot(screenshot_path)
    print(f"Đã lưu ảnh chụp: {screenshot_path}")

finally:
    driver.quit()
