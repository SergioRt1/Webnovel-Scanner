import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from logic.websites import Website
from logic.websites.normal_website import NormalWebsite
from logic.selenium_web import ScrapperSelenium

from utils import selenium, image


class NovelHall(NormalWebsite):
    def __init__(self, scrapper: ScrapperSelenium):
        selectors = {
            '_get_title': '#main > div > div.book-main.inner.mt30 > div.book-info > h1',
            '_get_description': '#main > div > div.book-main.inner.mt30 > div.book-info > div.intro > span.js-close-wrap',
            '_get_author': '#main > div > div.book-main.inner.mt30 > div.book-info > div.total.booktag > span:nth-child(2)',
            '_get_cover_img': '#main > div > div.book-main.inner.mt30 > div.book-img.hidden-xs > img',
            'get_table_content_clickable_element': '',
            'get_chapter_list': '#morelist',
            'get_chapter_content': '#htmlContent',
        }
        super().__init__(scrapper, Website.NovelHall, selectors)

    def _get_chapter_title(self, a):
        if a and a.text:
            return a.text.strip()
        return None

    def _get_cover_img(self, novel_title):
        img_src = self._get_image_src(self.selectors['_get_cover_img'])

        return image.download_with_screenshot(self.scrapper.driver, novel_title, img_src) if img_src else None

    def get_table_content_element(self) -> WebElement | None:
        return None

    def get_loading_delay(self) -> float:
        return 1.9

    def get_chapter_content(self):
        chapter_content = selenium.get_element(
            self.scrapper.driver,
            By.CSS_SELECTOR,
            self.selectors['get_chapter_content'],
        )
        return re.sub(r'\n+', '\n', chapter_content.text.strip())

