import os
import pickle
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Takes in the URL of a chegg page logs in and grabs the right material
def get_chegg_images(URL, user=None, password=None):

    chrome_options = Options()
    chrome_options.headless = True
    chrome_options.add_argument('window-size=1920,1080')
    chrome_options.add_argument('--user-data-dir=/home/joseph/chegg-bot/user')
    driver = webdriver.Chrome('./chromedriver', chrome_options=chrome_options)
    driver.get(url)
    input("finish")
    driver.quit()
    return None

url = "https://www.chegg.com/homework-help/questions-and-answers/consider-circuit--use-node-voltage-method-obtain-node-voltages-v1-v2-v3-use-linsolve-funct-q55827065"
url = "https://www.google.com"

images = get_chegg_images(url)
