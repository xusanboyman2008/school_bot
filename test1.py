import io
import time
import requests
from PIL import Image
import pytesseract
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1) Headless Chrome setup ---
opts = Options()
opts.add_argument("--headless")
opts.add_argument("--disable-gpu")
opts.add_argument("--window-size=1280,1024")

driver = webdriver.Chrome(options=opts)
driver.get("https://login.emaktab.uz/")

try:
    wait = WebDriverWait(driver, 20)

    # --- 2) Wait until ANY <img> with "captcha" in its src appears ---
    wait.until(lambda d: any(
        img.get_attribute("src") and "captcha" in img.get_attribute("src").lower()
        for img in d.find_elements(By.TAG_NAME, "img")
    ))

    captcha_el = next(
        img for img in driver.find_elements(By.TAG_NAME, "img")
        if img.get_attribute("src") and "captcha" in img.get_attribute("src").lower()
    )
    captcha_url = captcha_el.get_attribute("src")
    if captcha_url.startswith("/"):
        captcha_url = "https://login.emaktab.uz" + captcha_url

    # --- 4) Transfer cookies into requests.Session() ---
    sess = requests.Session()
    for c in driver.get_cookies():
        sess.cookies.set(c['name'], c['value'])

    # --- 5) Download the CAPTCHA image ---
    img_resp = sess.get(captcha_url)
    img = Image.open(io.BytesIO(img_resp.content))
    img.save("captcha_debug.png")  # debug: inspect this file if needed

    code =
    print(f"[+] OCR’d CAPTCHA: {code}")

    # --- 7) Fill form & submit ---
    driver.find_element(By.NAME, "login").send_keys("mamayusupovaziyodaxo")
    driver.find_element(By.NAME, "password").send_keys("12345678")
    driver.find_element(By.NAME, "captcha").send_keys(code)
    driver.find_element(By.CLASS_NAME, "login_btn").click()

    # --- 8) Verify success ---
    time.sleep(3)
    if "logout" in driver.page_source.lower():
        print("[✅] Login successful!")
    else:
        print("[❌] Login may have failed – check page content.")

finally:
    driver.quit()
