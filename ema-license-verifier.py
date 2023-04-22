from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from twocaptcha import TwoCaptcha
from bs4 import BeautifulSoup
from apscheduler.schedulers.background import BackgroundScheduler
from halo import Halo  # import Halo package
from dotenv import dotenv_values
import re
import atexit


scraped_electrician_ids = []
scraped_gas_workers_ids = []
scraped_cable_workers_ids = []


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
            browser.find_element(By.NAME, "captcha").send_keys(code)
            browser.find_element(By.NAME, "cmdSearchByName").click()
        # use Halo to display success message
        spinner.succeed('CAPTCHA Bypass complete')


def scrape_electrical_worker_data(browser):
    # use Halo to display spinner
    with Halo(text='2. Scraping Electical Worker data...', spinner='dots') as spinner:
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
        spinner.succeed('Scraping Electical Worker complete')


def scrape_gas_service_worker_data(browser):
    # use Halo to display spinner
    with Halo(text='2. Scraping Gas Service Worker data...', spinner='dots') as spinner:
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
        spinner.succeed('Scraping Gas Service Worker complete')


def scrape_cable_worker_data(browser):
    # use Halo to display spinner
    with Halo(text='2. Scraping Cable Detection Worker data...', spinner='dots') as spinner:
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
            scraped_cable_workers_ids.append(data[0])

        # use Halo to display success message
        spinner.succeed('Scraping Cable Detection Worker complete')


def scrape():
    # Launch browser
    browser = launch_browser()
    try:
        selectElectricalTagClass = browser.find_element(
            By.LINK_TEXT, "Electrical Worker").click()
    except:
        print("Unable to locate selectElectricalTagClass, will continue as normal...")

    selectElectricalRadioButton = browser.find_element(
        By.ID, "seachAllRadio").click()
    selectDropDown = Select(browser.find_element(
        By.NAME, "WorkerType")).select_by_value("OFFERE")

    # Bypass CAPTCHA for Electrician who offer consumer services
    bypass_captcha(browser)
    scrape_electrical_worker_data(browser)
    print("Scraped Electrical Workers:", scraped_electrician_ids)

    # Scrape Gas Service Workers who offer consumer services
    selectGasTagClass = browser.find_element(
        By.LINK_TEXT, "Gas Service Worker").click()
    selectGasDropdown = Select(browser.find_element(
        By.NAME, "WorkerType")).select_by_value("OFFERG")
    selectResidentialCheckbox = browser.find_element(
        By.ID, "chkResidential").click()
    selectchkNonResidentialCheckbox = browser.find_element(
        By.ID, "chkNonResidential").click()
    selectchkAllGasInstallationCheckbox = browser.find_element(
        By.ID, "chkAllGasInstallation").click()

    # Bypass CAPTCHA for Gas Service Workers who offer consumer services
    bypass_captcha(browser)
    scrape_gas_service_worker_data(browser)
    print("Scraped Gas Workers:", scraped_gas_workers_ids)

    # Scrape Cable Detection Workers
    selectCableTagClass = browser.find_element(
        By.LINK_TEXT, "Cable Detection Worker").click()
    # selectCableRadioButton = browser.find_element(
    #     By.ID, "seachAllRadio").click()

    bypass_captcha(browser)
    scrape_cable_worker_data(browser)
    print("Scraped Cable Workers:", scraped_cable_workers_ids)

    # check if any of the arrays are empty
    check_if_lists_are_empty()


def check_if_lists_are_empty():
    # check if any of the arrays are empty
    lists_to_check = [scraped_electrician_ids,
                      scraped_gas_workers_ids, scraped_cable_workers_ids]
    while any(not lst for lst in lists_to_check):
        print("One or more lists are empty. Scraping data again...")
        scrape()
        print("Scraping complete. Checking lists again...")
        lists_to_check = [scraped_electrician_ids,
                          scraped_gas_workers_ids, scraped_cable_workers_ids]

    print("\033[32mAll lists are non-empty. Everything is ready to go. \033[0m")

    # create a dictionary to store the license IDs and their corresponding list names
    id_to_list = {}
    for id in scraped_electrician_ids:
        id_to_list[id] = 'Electrician'
    for id in scraped_gas_workers_ids:
        id_to_list[id] = 'Gas Worker'
    for id in scraped_cable_workers_ids:
        id_to_list[id] = 'Cable Worker'

    while True:
        user_input = input(
            "\033[33mEnter the license ID or type 'q' to quit: \033[0m")
        if user_input.lower() == 'q':
            # quit chrome browser
            browser.quit()
            break
        # check the dictionary for user_input
        if user_input in id_to_list:
            print("\033[32m{} License ID found: {}.\033[0m".format(
                id_to_list[user_input], user_input))
        else:
            print("\033[31mLicense ID {} not found.\033[0m".format(user_input))


if __name__ == '__main__':
    # Scrape data once before starting the scheduler
    scrape()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scrape, trigger="interval", hours=24)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
