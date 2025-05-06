import datetime
import time
from io import BytesIO

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chromium.service import ChromiumService  # Use ChromiumService for Chromium browsers
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager  # We're still using this to install Chromium
from captcha_ai import extract_numbers_from_clean_image
from models import get_login_all

successful_logins = 0
wrong_logins = []

def eschool(login, password, school):
    global successful_logins, wrong_logins

    # Use Chromium options to configure either Chrome or Brave
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--headless')

    # Specify the path to Chromium browser (if needed, depending on your system)
    options.binary_location = '/usr/bin/chromium-browser'  # Path for Chromium

    # Initialize the ChromiumService for proper Chromium driver management
    driver = webdriver.Chrome(service=ChromiumService(ChromeDriverManager().install()), options=options)

    def is_logged_in():
        time.sleep(0.3)
        return driver.current_url not in ["https://login.emaktab.uz/", "https://login.emaktab.uz/login/"]

    def solve_captcha_if_needed():
        wait = WebDriverWait(driver, 20)
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

        sess = requests.Session()
        for c in driver.get_cookies():
            sess.cookies.set(c['name'], c['value'])

        img_resp = sess.get(captcha_url)
        img = Image.open(BytesIO(img_resp.content))
        img.save("captcha_debug.png")

        captcha_code = extract_numbers_from_clean_image("captcha_debug.png")
        return captcha_code

    try:
        driver.get("https://login.emaktab.uz")

        driver.find_element(By.NAME, "login").clear()
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "login").send_keys(login)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "[data-test-id='login-button']").click()

        if is_logged_in():
            print("✅ Login successful on first attempt.")
            successful_logins += 1
        else:
            code = solve_captcha_if_needed()
            print(f"🔁 Login failed. Retrying with CAPTCHA code: {code}")
            captcha_input = driver.find_element(By.NAME, 'Captcha.Input')

            if not captcha_input.is_displayed():
                wrong_logins.append(f"{login}:{password}:{school}")
                return

            captcha_input.clear()
            captcha_input.send_keys(code)
            driver.find_element(By.CSS_SELECTOR, "[data-test-id='login-button']").click()

            if is_logged_in():
                print("✅ Login successful on retry.")
                successful_logins += 1
            else:
                print("❌ Login failed after retry.")
                wrong_logins.append(f'{login}:{password}:{school}')

    except Exception as e:
        print(f"❌ Error during login for {login}: {e}")
        wrong_logins.append(f'{login}:{password}:{school}')
    finally:
        driver.quit()

async def main_eschool():
    login_data = await get_login_all()
    a = 0
    start_time = datetime.datetime.now()

    for i in login_data:
        a += 1
        print('total logins:', a)
        print('login:', i.login, 'password:', i.password)
        eschool(i.login, i.password, i.school_number)
        print('time spent:', datetime.datetime.now() - start_time, 'for', a)

    print("❌ Failed logins:", wrong_logins)
    return successful_logins, wrong_logins
