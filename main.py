import os
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

path = os.path.join(os.getcwd(), 'chromedriver')

option = Options()
prefs = {"profile.default_content_setting_values.notifications": 2}
option.add_experimental_option("prefs", prefs)
option.add_argument( "start-maximized" )
option.add_argument( "--disable-infobars" )
option.add_argument( "--disable-extensions" )

print(path)
driver = webdriver.Chrome(executable_path=path, options=option)
driver.maximize_window()

LOGIN_URL = 'https://www.upwork.com/ab/account-security/login'
USERNAME = 'chesterdealday@gmail.com'
PASSWORD = '7w5i9oxkgr3J'

driver.get(LOGIN_URL)
time.sleep(3)
input_username = driver.find_element_by_xpath('//*[@id="login_username"]')
input_username.send_keys(USERNAME)
time.sleep(2)
continue_button = driver.find_element_by_xpath('//*[@id="login_password_continue"]')
continue_button.click()
time.sleep(5)
