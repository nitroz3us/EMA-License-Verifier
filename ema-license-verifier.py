from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from halo import Halo  # import Halo package
from dotenv import dotenv_values
import atexit


scraped_electrician_ids = []
scraped_gas_workers_ids = []


def launch_browser():
    global browser  # declare browser as a global variable
    if 'browser' in globals():  # check if browser already exists
        return browser
    else:  # create a new browser instance if it doesn't exist
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--window-size=700,700')
        chrome_options.add_experimental_option("detach", True)
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        browser = webdriver.Chrome(
            options=chrome_options, executable_path='/usr/local/bin/chromedriver')  # for macOS/linux, download chromedriver beforehand and place it in /usr/local/bin
        browser = webdriver.Chrome(options=chrome_options)
        browser.get(
            "https://elise.ema.gov.sg/elise/findworkerservlet?Operation=Get&Item=EL")
        return browser


# def launch_browser():
#     chrome_options = Options()
#     chrome_options.add_argument('--no-sandbox')
#     chrome_options.add_argument('--window-size=700,700')
#     chrome_options.add_argument('--headless')
#     chrome_options.add_argument('--disable-gpu')
#     chrome_options.add_argument('--disable-dev-shm-usage')
#     # browser = webdriver.Chrome(options=chrome_options, executable_path='/usr/local/bin/chromedriver')
#     browser = webdriver.Chrome(options=chrome_options)
#     browser.get(
#         "https://elise.ema.gov.sg/elise/findworkerservlet?Operation=Get&Item=EL")
#     return browser


def bypass_captcha(browser):
    with Halo(text='1. Bypassing CAPTCHA', spinner='dots') as spinner:  # use Halo to display spinner
        captchaImg = browser.find_element(By.ID, "img")
        captchaImg.screenshot('./captchas/captcha.png')
        config = dotenv_values(".env")
        api_key = config['API_KEY']  # get API key from .env file
        solver = TwoCaptcha(api_key)
        try:
            result = solver.normal('./captchas/captcha.png')
        except Exception as e:
            print(e)
        else:
            code = result['code']
            # print(code)
            browser.find_element(By.NAME, "captcha").send_keys(code)
            browser.find_element(By.NAME, "cmdSearchByName").click()
        # use Halo to display success message
        spinner.succeed('CAPTCHA Bypass complete')


def scrape_electrical_worker_data(browser):
    # use Halo to display spinner
    with Halo(text='2. Scraping electical worker data...', spinner='dots') as spinner:
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
            data = [re.sub(r'\d+(?=\(Tel\))\(Tel\)', '', item)
                    for item in data]
            # remove any trailing whitespace
            data = [item.strip() for item in data]
            # remove (hp)
            data = [re.sub(r'\(Hp\)', '', item) for item in data]
            # assume the license ID is the first element in the array
            # only show license ID for now
            scraped_electrician_ids.append(data[0])

        # use Halo to display success message
        spinner.succeed('Scraping electrical worker complete')


def scrape_gas_service_worker_data(browser):
    # use Halo to display spinner
    with Halo(text='2. Scraping gas service worker data...', spinner='dots') as spinner:
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
            data = [re.sub(r'\d+(?=\(Tel\))\(Tel\)', '', item)
                    for item in data]
            # remove any trailing whitespace
            data = [item.strip() for item in data]
            # remove (hp)
            data = [re.sub(r'\(Hp\)', '', item) for item in data]
            # assume the license ID is the first element in the array
            scraped_gas_workers_ids.append(data[0])

        # use Halo to display success message
        spinner.succeed('Scraping gas service worker complete')


def scrape():
    # Launch browser
    browser = launch_browser()
    selectRadioButton = browser.find_element(By.ID, "seachAllRadio").click()
    # Select dropdown for Electrician who offer consumer services
    selectDropDown = Select(browser.find_element(
        By.NAME, "WorkerType")).select_by_value("OFFERE")

    # Bypass CAPTCHA for Electrician who offer consumer services
    bypass_captcha(browser)
    scrape_electrical_worker_data(browser)
    print("Scraped gas workers:", scraped_electrician_ids)

    # Scrape gas service workers
    selectTagClass = browser.find_element(
        By.LINK_TEXT, "Gas Service Worker").click()
    selectResidentialCheckbox = browser.find_element(
        By.ID, "chkResidential").click()
    selectchkNonResidentialCheckbox = browser.find_element(
        By.ID, "chkNonResidential").click()
    selectchkAllGasInstallationCheckbox = browser.find_element(
        By.ID, "chkAllGasInstallation").click()

    # Bypass CAPTCHA for Gas Service Workers who offer consumer services
    bypass_captcha(browser)
    scrape_gas_service_worker_data(browser)
    print("Scraped gas workers:", scraped_gas_workers_ids)

    while True:
        user_input = input(
            "\033[33mEnter the license ID or type 'q' to quit: \033[0m")
        if user_input.lower() == 'q':
            break
        # check scraped_electrician_ids for user_input
        if user_input in scraped_electrician_ids or user_input in scraped_gas_workers_ids:
            print("\033[32mLicense ID {} found.\033[0m".format(user_input))
        else:
            print("\033[31mLicense ID {} not found.\033[0m".format(user_input))


if __name__ == '__main__':
    # Scrape data once before starting the scheduler
    scrape()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scrape, trigger="interval", hours=24)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
