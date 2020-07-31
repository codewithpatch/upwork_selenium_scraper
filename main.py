import os
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import *

from items import FreelancerScraperItem
from pipelines import FreelancerScraperPipeline


class FreelancerScraper:
    login_url = 'https://www.freelancer.com/login'
    username = ''
    password = ''

    def __init__(self):
        self.path = os.path.join(os.getcwd(), 'chromedriver')
        self.option = self.__set_option__()
        self.driver = webdriver.Chrome(executable_path=self.path, options=self.option)
        self.raw_search_url = 'https://www.freelancer.com/search/{}/?ngsw-bypass=&w=f&q={}'
        # self.raw_search_url = 'https://www.freelancer.com/search/{}/any_skill/any_country/2/?ngsw-bypass=&w=f&q={}'

    def __set_option__(self):
        option = Options()
        prefs = {"profile.default_content_setting_values.notifications": 2}
        option.add_argument('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                            'Chrome/84.0.4147.89 Safari/537.36')
        option.add_experimental_option("prefs", prefs)
        option.add_argument("start-maximized")
        option.add_argument("--disable-infobars")
        option.add_argument("--disable-extensions")

        return option

    def login(self):
        driver = self.driver
        driver.maximize_window()
        driver.get(self.login_url)
        time.sleep(5)

        input_username = driver.find_element_by_xpath(
            '/html/body/app-root/app-logged-out-shell/app-login-page/fl-page-layout/main/fl-container/fl-page-layout'
            '-single/app-login/fl-card/fl-bit/fl-bit/app-credentials-form/form/fl-input[1]/fl-bit/fl-bit/input')
        input_username.send_keys(self.username)
        time.sleep(2)

        input_password = driver.find_element_by_xpath(
            '/html/body/app-root/app-logged-out-shell/app-login-page/fl-page-layout/main/fl-container/fl-page-layout'
            '-single/app-login/fl-card/fl-bit/fl-bit/app-credentials-form/form/fl-input[2]/fl-bit/fl-bit/input')
        input_password.send_keys(self.password)
        time.sleep(2)

        submit_button = driver.find_element_by_xpath(
            '/html/body/app-root/app-logged-out-shell/app-login-page/fl-page-layout/main/fl-container/fl-page-layout'
            '-single/app-login/fl-card/fl-bit/fl-bit/app-credentials-form/form/app-login-signup-button/fl-button'
            '/button')
        submit_button.click()
        time.sleep(3)

    def search_category(self, type, category):
        suffix_category = '%20'.join(category.split())
        url = self.raw_search_url.format(type, suffix_category)
        self.driver.get(url)
        time.sleep(5)

        return self.driver.page_source

    def go_next_page(self):
        current_url = self.driver.current_url
        next_page_button = ''
        for i in range(8, 11):
            try:
                next_page_button = self.driver.find_element_by_xpath(
                    '//*[@id="search-results"]/div[2]/ul/li[{}]/a'.format(i)
                )
                time.sleep(0.5)
                if next_page_button.text == 'Next':
                    break
            except:
                for e in range(4, 8):
                    try:
                        next_page_button = self.driver.find_element_by_xpath(
                            '//*[@id="search-results"]/div[2]/ul/li[{}]/a'.format(e)
                        )
                        time.sleep(0.5)

                        if next_page_button.text == 'Next':
                            break
                    except:
                        break

        if next_page_button:
            next_page_button.click()
            time.sleep(3)

            next_page_url = self.driver.current_url
            if current_url == next_page_url:
                print("No more next page")
                return 0

            return self.driver.page_source
        else:
            return 0

    def get_freelancer_link(self, page_source):
        url_list = []
        soup = BeautifulSoup(page_source, 'lxml')
        freelancers = soup.findAll('div', attrs={'class': 'Card-body'})
        for freelancer in freelancers:
            freelancer_url = 'https://www.freelancer.com' + freelancer.find('a')['href']
            if freelancer_url in freelancer_url_list:
                continue

            url_list.append(freelancer_url)

        return url_list

    def get_freelancer_data(self, url):
        freelancer_data = FreelancerScraperItem()
        self.driver.get(url)
        time.sleep(3)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')

        title = soup.find('h2', attrs={'class': 'ng-star-inserted'})
        if title:
            freelancer_data.title = title.text

        hourly_rate = soup.find('div', attrs={
            'class': 'NativeElement ng-star-inserted',
            'data-color': 'dark',
            'role': 'paragraph',
            'data-size': 'xsmall',
            'data-weight': 'bold',
            'data-style': 'normal',
        })
        if hourly_rate:
            freelancer_data.hourly_rate = hourly_rate.text.strip()

        description = soup.findAll('div', attrs={
            'class': 'NativeElement ng-star-inserted',
            'data-color': 'dark',
            'role': 'paragraph',
            'data-size': 'xsmall',
            'data-weight': 'normal',
            'data-style': 'normal',
            'data-line-break': 'false'
        })
        if description:
            description_list = soup.findAll('div', attrs={
                'class': 'NativeElement ng-star-inserted',
                'data-color': 'dark',
                'role': 'paragraph',
                'data-size': 'xsmall',
                'data-weight': 'normal',
                'data-style': 'normal',
                'data-line-break': 'false'
            })
            descriptions = [text.text for text in description_list]
            description = descriptions[13]
            location = descriptions[12]
            freelancer_data.description = description
            freelancer_data.location = location

        education = soup.find('h2', attrs={
            'class': 'ng-star-inserted',
            'data-color': 'dark',
            'data-size': 'small',
            'data-truncate': 'false',
            'data-weight': 'bold'
        })
        if education:
            freelancer_data.education = education.text

        freelancer_data.total_earnings = 'No available data'
        freelancer_data.total_jobs = 'No available data'

        # Skills and expertise
        while True:
            try:
                view_more_button = self.driver.find_element_by_xpath(
                    '/html/body/app-root/app-logged-in-shell/div/div[2]/app-user-profile-wrapper/app-user-profile/fl-bit[2]/fl-bit[2]/fl-container/fl-grid/fl-col[3]/app-user-profile-skills/fl-card/fl-bit/fl-bit[2]/fl-link/button'
                ).click()
            except:
                break
        skills_and_expertise = soup.findAll('fl-bit', attrs={
            'class': 'UserProfileSkill',
        })
        if skills_and_expertise:
            freelancer_data.skills_and_expertise = [text.text for text in skills_and_expertise]

        return freelancer_data

    def model_to_dict(self, model):
        return {
            'title': model.title,
            'hourly rate': model.hourly_rate,
            'description': model.description,
            'location': model.location,
            'education': model.education,
            'total earnings': model.total_earnings,
            'total jobs': model.total_jobs,
            'skills and expertise': model.skills_and_expertise,
            'work history': model.work_history,
        }

    def close_selenium(self):
        self.driver.quit()


if __name__ == '__main__':
    scraper = FreelancerScraper()
    pipeline = FreelancerScraperPipeline()

    types = ['projects', 'users']
    categories = [
        'Machine Learning',
        'Deep learning',
        'Data visualization',
        'Data processing',
        'Data engineering',
        'Data analytics',
        'Data mining',
        'Data science',
        'Data warehousing',
        'Business Intelligence',
        'Big data',
        'Data pipelines',
        'Computer vision',
        'Natural language processing'
    ]
    scraper.login()

    for type in types:
        if type != 'users':
            continue

        # freelancer_url_list = []
        for category in categories:
            print("Searching category:", category)
            freelancer_url_list = []
            if len(freelancer_url_list) > 100:
                continue

            # TODO: FIX THIS BLOCK, the script is looping only by the length of freelancers variable
            category_source = scraper.search_category(type, category)
            soup = BeautifulSoup(category_source, 'lxml')
            # soup.find('div', attrs={'class': 'info-card-inner info-card-inner--user'})
            freelancers = soup.findAll('div', attrs={'class': 'Card-body'})
            for freelancer in freelancers:
                freelancer_url_list = list(set(freelancer_url_list))
                print("Freelancer count:", len(freelancer_url_list), "...")
                if len(freelancer_url_list) > 100:
                    break

                frelancer_url = 'https://www.freelancer.com' + freelancer.find('a')['href']
                if freelancer_url_list not in freelancer_url_list:
                    freelancer_url_list.append(frelancer_url)

            while True:
                time.sleep(2)
                next_page_source = scraper.go_next_page()
                freelancer_url_list = list(set(freelancer_url_list))
                print("Freelancer count:", len(freelancer_url_list), "...")
                if len(freelancer_url_list) > 100:
                    print("100 freelancers reached")
                    break

                if next_page_source:
                    freelancer_urls = scraper.get_freelancer_link(next_page_source)
                    freelancer_url_list += freelancer_urls
                else:
                    print("No more next page!")
                    break

            # TODO: WORK ON freelancer_url_list: visit each url and get data, and save to data model
            pipeline.open_spider()
            time.sleep(1)
            count = 0
            for url in freelancer_url_list:
                freelancer_data = scraper.get_freelancer_data(url)
                freelancer_data = scraper.model_to_dict(freelancer_data)

                pipeline.process_item(freelancer_data)
                time.sleep(1)

                count += 1
                if count == 5:
                    break

    pipeline.close_spider()
    scraper.close_selenium()
