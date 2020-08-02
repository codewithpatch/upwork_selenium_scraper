import os
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

from items import FreelancerScraperItem, ProjectScraperItem
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

    def search_category(self, typ, category):
        suffix_category = '%20'.join(category.split())
        url = self.raw_search_url.format(typ, suffix_category)
        self.driver.get(url)
        time.sleep(5)
        try:
            self.driver.find_element_by_xpath(
                '//*[@id="main"]/section/fl-search/div/div[1]/form/ol[2]/fl-projects-filter/li/ul/li[2]/div[2]/button'
            ).click()
            time.sleep(3)
        except:
            pass

        return self.driver.page_source

    def go_next_page(self, typ):
        current_url = self.driver.current_url
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')
        disabled_buttons = soup.findAll('li', attrs={'ng-repeat': 'page in pages', 'class': 'disabled'})
        if disabled_buttons:
            disabled_buttons = [text.text for text in disabled_buttons]
            if 'Next' in disabled_buttons:
                print("Next page is disabled")
                return 0

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
                        continue

        if next_page_button:
            try:
                next_page_button.click()
                time.sleep(4)
            except:
                print("Can't click next button")
                return 0

            next_page_url = self.driver.current_url
            if typ == 'users':
                if current_url == next_page_url:
                    print("No more next page")
                    return 0

            return self.driver.page_source
        else:
            return 0

    def get_block_link(self, page_source):
        url_list = []
        soup = BeautifulSoup(page_source, 'lxml')
        blocks = soup.findAll('div', attrs={'class': 'Card-body'})
        if not blocks:
            blocks = soup.findAll('li', attrs={'ng-repeat': 'project in search.results.projects'})
        for block in blocks:
            block_url = 'https://www.freelancer.com' + block.find('a')['href']
            if block_url in url_list:
                continue

            url_list.append(block_url)

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

        # Description
        try:
            self.driver.find_element_by_xpath('//*[@class="ReadMoreButton"]').click()
        except:
            pass

        description = soup.find('app-user-profile-summary-description')
        if description:
            freelancer_data.description = description.text

        # Location
        location = soup.find('fl-col', attrs={'class': 'SupplementaryInfo'})
        if location:
            freelancer_data.location = location.text

        # Eduction
        education = soup.findAll('fl-bit', attrs={'class': 'Degree'})
        if education and "Education" in soup.text:
            freelancer_data.education = [text.text for text in education]

        # Total earnings and total jobs
        freelancer_data.total_earnings = 'No available data'
        freelancer_data.total_jobs = 'No available data'

        # Skills and expertise
        while True:
            try:
                self.driver.find_element_by_xpath(
                    '/html/body/app-root/app-logged-in-shell/div/div['
                    '2]/app-user-profile-wrapper/app-user-profile/fl-bit[2]/fl-bit[2]/fl-container/fl-grid/fl-col['
                    '3]/app-user-profile-skills/fl-card/fl-bit/fl-bit[2]/fl-link/button '
                ).click()
            except:
                break
        skills_and_expertise = soup.findAll('fl-bit', attrs={
            'class': 'UserProfileSkill',
        })
        if skills_and_expertise:
            freelancer_data.skills_and_expertise = [text.text for text in skills_and_expertise]

        return freelancer_data

    def get_project_data(self, url):
        project_data = ProjectScraperItem()
        self.driver.get(url)
        time.sleep(4)
        page_source = self.driver.page_source
        soup = BeautifulSoup(page_source, 'lxml')

        # title
        title = soup.find('h1')
        if title:
            project_data.title = title.text

        # project_rate
        project_rate = soup.find('fl-bit', attrs={'class': 'ProjectViewDetails-budget'})
        if project_rate:
            project_rate = project_rate.text
            project_data.project_rate = project_rate.strip().split(' \n\n ')[0]

        # description
        description = soup.find('fl-bit', attrs={'class': 'ProjectDescription'})
        if description:
            project_data.description = description.text

        # location
        employer_info = employer_info = soup.find('app-employer-info')
        if employer_info:
            location = employer_info.find('fl-bit', attrs={'class': 'BitsListItemHeader First'})
            if location:
                project_data.location = location.text.strip()

        skills_and_expertise = soup.findAll('fl-tag', attrs={'fltrackinglabel': 'ProjectSkillTag'})
        if skills_and_expertise:
            project_data.skills_and_expertise = [text.text.strip() for text in skills_and_expertise]

        return project_data

    def model_to_dict(self, typ, model):
        if typ == 'users':
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
        else:
            return {
                'title': model.title,
                'project rate': model.project_rate,
                'description': model.description,
                'location': model.location,
                'skills and expertise': model.skills_and_expertise,
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
    for typ in types:
        # if typ == 'users':
        #     continue

        pipeline.open_spider(typ)
        for category in categories:
            print("Searching category:", category)
            url_list = []
            if len(url_list) > 100:
                continue

            category_source = scraper.search_category(typ, category)
            soup = BeautifulSoup(category_source, 'lxml')
            blocks = ''
            if typ == 'users':
                blocks = soup.findAll('div', attrs={'class': 'Card-body'})
            else:
                blocks = soup.findAll('li', attrs={'ng-repeat': 'project in search.results.projects'})

            for block in blocks:
                url_list = list(set(url_list))
                print("block count:", len(url_list), "...")
                if len(url_list) > 100:
                    break

                page_url = 'https://www.freelancer.com' + block.find('a')['href']
                if url_list not in url_list:
                    url_list.append(page_url)

            while True:
                if len(blocks) < 9:
                    print("type - {}, category - {}: No 2nd page".format(typ, category))
                    break

                time.sleep(2)
                next_page_source = scraper.go_next_page(typ)
                url_list = list(set(url_list))
                print("block count:", len(url_list), "...")
                if len(url_list) > 100:
                    print("100 freelancers reached")
                    break

                if next_page_source:
                    new_urls = scraper.get_block_link(next_page_source)
                    url_list += new_urls
                else:
                    print("No more next page!")
                    break

            # freelancer_url_list: visit each url and get data, and save to data model
            time.sleep(1)
            count = 0
            for url in url_list:
                data_dict = {}
                if typ == 'users':
                    freelancer_data = scraper.get_freelancer_data(url)
                    data_dict = scraper.model_to_dict(freelancer_data)
                elif typ == 'projects':
                    project_data = scraper.get_project_data(url)
                    data_dict = scraper.model_to_dict(typ, project_data)
                    print(data_dict)

                pipeline.process_item(data_dict)
                time.sleep(1)

                count += 1
                print("{} out of {}".format(count, len(url_list)))

        pipeline.close_spider()
    scraper.close_selenium()
