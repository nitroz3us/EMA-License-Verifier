from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
from bs4 import BeautifulSoup
import re
import atexit
import os

from apscheduler.schedulers.background import BackgroundScheduler


def launch_browser():
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=700,700')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # browser = webdriver.Chrome(options=chrome_options)
    # browser = webdriver.Chrome(options=chrome_options, executable_path='/usr/local/bin/chromedriver')
    browser = webdriver.Chrome(chrome_options=chrome_options)
    browser.get(
        "https://elise.ema.gov.sg/elise/findworkerservlet?Operation=Get&Item=EL")
    return browser


def bypass_captcha(browser):
    print("2. Bypassing CAPTCHA...")
    captchaImg = browser.find_element(By.ID, "img")
    captchaImg.screenshot('./captchas/captcha.png')
    # api_key = os.getenv('EMA_API_2CAPTCHA')
    api_key = 'EMA_API_2CAPTCHA'
    print(api_key)  # remove this later
    solver = TwoCaptcha(api_key)
    try:
        result = solver.normal('./captchas/captcha.png')
    except Exception as e:
        print(e)
    else:
        code = result['code']
        print(code)
        browser.find_element(By.NAME, "captcha").send_keys(code)
        browser.find_element(By.NAME, "cmdSearchByName").click()


def scrape_data(browser):
    print("3. Scraping data...")
    page_source = browser.page_source
    soup = BeautifulSoup(page_source, "lxml")

    rows = soup.find_all("tr", class_="tabledetail")
    for row in rows:
        cells = row.find_all("td")
        data = [cell.get_text(separator='<br>', strip=True).replace(
            '<br>', ' ') for cell in cells]
        data.pop(0)  # remove first index
        # remove email
        data = [re.sub(r'\S+@\S+', '', item) for item in data]
        # remove number before (Tel) and (Tel) itself
        data = [re.sub(r'\d+(?=\(Tel\))\(Tel\)', '', item) for item in data]
        # remove any trailing whitespace
        data = [item.strip() for item in data]
        # remove (hp)
        data = [re.sub(r'\(Hp\)', '', item) for item in data]
        print(data)


# @app.route("/ema", methods=['POST'])
def scrape():
    # Launch browser
    print("1. Launching Browser...")
    browser = launch_browser()
    selectRadioButton = browser.find_element(By.ID, "seachAllRadio")
    selectRadioButton.click()
    # Select dropdown for Electrician who offer consumer services
    selectDropDown = Select(browser.find_element(By.NAME, "WorkerType"))
    selectDropDown.select_by_value("OFFERE")

    # Bypass CAPTCHA
    bypass_captcha(browser)
    # Use beautifulsoup to scrap the data
    scrape_data(browser)
    # pass
    print("Scraping completed.")


if __name__ == '__main__':
    # Scrape data once before starting the scheduler
    scrape()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scrape, trigger="interval", hours=24)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
