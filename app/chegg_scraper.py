import os
import pickle

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Takes in the URL of a chegg page logs in and grabs the right material
def get_chegg_images(URL, user=None, password=None):
    # First we need to initialize the driver
    # Setup Options before driver
    chrome_options = Options()
    chrome_options.headless = True
    
    chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-blink-features")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-web-security")
    #chrome_options.add_argument("--proxy-server=localhost:8080") # Not sure if this is really needed actually...
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-data-dir=/home/joseph/g3-bot/app/user")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36")
    driver = webdriver.Chrome('./chromedriver', chrome_options=chrome_options)



    # Now we search for our content
    driver.get(url)
    class_selector="div.answer-given-body"
    content = driver.find_elements_by_class_name(class_selector)
    print(content)

    input("finish")
    driver.quit()

    return None

url = "https://www.josephghanimah.com"
url = "https://intoli.com/blog/not-possible-to-block-chrome-headless/chrome-headless-test.html"
url = "https://www.chegg.com/homework-help/questions-and-answers/consider-circuit--use-node-voltage-method-obtain-node-voltages-v1-v2-v3-use-linsolve-funct-q55827065"


#get_chegg_images(url)