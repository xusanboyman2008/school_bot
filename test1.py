import datetime
import time
from io import BytesIO

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from captcha_ai import extract_numbers_from_clean_image
from models import get_login_all

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(
    service=Service("/usr/bin/chromedriver"),
    options=options
)




successful_logins = 0
wrong_logins = []


def eschool(login, password, school):
    global successful_logins, wrong_logins

    # Each user gets a new WebDriver session
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    # options.add_argument('--headless')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    def is_logged_in():
        time.sleep(0.3)
        if driver.current_url == "https://login.emaktab.uz/" or driver.current_url == "https://login.emaktab.uz/login/":
            return False
        return True

    def solve_captcha_if_needed():
        # Step 1: Wait for any <img> with "captcha" in its src to appear.
        wait = WebDriverWait(driver, 20)
        wait.until(lambda d: any(
            img.get_attribute("src") and "captcha" in img.get_attribute("src").lower()
            for img in d.find_elements(By.TAG_NAME, "img")
        ))

        # Step 2: Find the CAPTCHA image element.
        captcha_el = next(
            img for img in driver.find_elements(By.TAG_NAME, "img")
            if img.get_attribute("src") and "captcha" in img.get_attribute("src").lower()
        )

        # Step 3: Get the CAPTCHA image URL.
        captcha_url = captcha_el.get_attribute("src")
        if captcha_url.startswith("/"):
            captcha_url = "https://login.emaktab.uz" + captcha_url

        # Step 4: Transfer cookies from Selenium to requests.Session() for maintaining session.
        sess = requests.Session()
        for c in driver.get_cookies():
            sess.cookies.set(c['name'], c['value'])

        # Step 5: Download the CAPTCHA image using requests.
        img_resp = sess.get(captcha_url)
        img = Image.open(BytesIO(img_resp.content))

        # Save image for debugging (optional)
        img.save("captcha_debug.png")

        # Step 6: Pass the image to your CAPTCHA-solving function.
        captcha_code = extract_numbers_from_clean_image("captcha_debug.png")  # Pass the file or image path.
        return captcha_code

    try:
        driver.get("https://login.emaktab.uz")

        driver.find_element(By.NAME, "login").clear()
        driver.find_element(By.NAME, "password").clear()
        driver.find_element(By.NAME, "login").send_keys(login)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "[data-test-id='login-button']").click()
        print(len(driver.get_cookies()))
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
            captcha_input.clear()  # Clear any existing code in the input field
            captcha_input.send_keys(code)  # Send the CAPTCHA code
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
    login = await get_login_all()
    a= 0
    str = datetime.datetime.now()
    for i in login:
        a+=1
        print('total logins: ',a)
        print('login', i.login, 'password', i.password)
        eschool(i.login, i.password, i.school_number)
    print('time spend',datetime.datetime.now() - str,'for',a)
    print(wrong_logins)
    return successful_logins, wrong_logins
