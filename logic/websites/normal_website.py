import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from logic.entities import Chapter
from logic.websites import Website, BasicWebsite
from utils import image, selenium


class NormalWebsite(BasicWebsite):
    def __init__(self, driver: webdriver.Chrome, website: Website, selectors: dict = None):
        super().__init__(driver, website)
        self.selectors = selectors

    def _get_title(self):
        return self._get_element_text(self.selectors['_get_title'])

    def _get_description(self):
        return self._get_element_text(self.selectors['_get_description'])

    def _get_author(self):
        return self._get_element_text(self.selectors['_get_author'])

    def _get_cover_img(self, novel_title):
        img_src = self._get_image_src(self.selectors['_get_cover_img'])
        if img_src:
            image_path, image_name = image.get_path_and_name(img_src, novel_title)

            response = requests.get(img_src)
            if response.status_code != 200:
                return None

            with open(image_path, 'wb') as f:
                f.write(response.content)
            return image_name
        return None

    def get_table_content_element(self) -> WebElement:
        return selenium.get_element(
            self.driver,
            By.CSS_SELECTOR,
            self.selectors['get_table_content_clickable_element'],
        )

    def get_chapter_list(self) -> [Chapter]:
        content = selenium.get_element(
            self.driver,
            By.CSS_SELECTOR,
            self.selectors['get_chapter_list'],
        )
        if content:
            a_tags = content.find_elements(By.TAG_NAME, 'a')
            return [Chapter(a.get_attribute('title'), a.get_attribute('href')) for a in a_tags]

    def get_chapter_content(self):
        chapter_content = selenium.get_element(
            self.driver,
            By.CSS_SELECTOR,
            self.selectors['get_chapter_content'],
        )

        return '\n'.join(p.text for p in chapter_content.find_elements(By.TAG_NAME, 'p')).strip()
