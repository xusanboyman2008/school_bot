import asyncio
import datetime
import time
from io import BytesIO

import requests
from PIL import Image
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from captcha_ai import extract_numbers_from_clean_image
from models import get_login_all

successful_logins = 0
wrong_logins = []

def eschool(login, password, school):
    global successful_logins, wrong_logins

    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = uc.Chrome(options=options)

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
            captcha_input = driver.find_element(By.NAME, 'Captcha.Input')
            print(f"🔁 Login failed. Retrying with CAPTCHA code: {code}")
            if not captcha_input.is_displayed():
                print(f"🔁 Login failed and no captcha found. Retrying with CAPTCHA code: {code}")
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

    for i in login_data[60:]:
        a += 1
        print('total logins:', a,'wrong logins: ',len(wrong_logins))
        print('login:', i.login, 'password:', i.password)
        eschool(i.login, i.password, i.school_number)
        print('time spent:', datetime.datetime.now() - start_time, 'for', a)

    print("❌ Failed logins:", wrong_logins)
    return successful_logins, wrong_logins

if __name__ == '__main__':
    asyncio.run(main_eschool())