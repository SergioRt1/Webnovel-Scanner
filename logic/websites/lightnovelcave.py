import time

from selenium import webdriver
from selenium.webdriver.common.by import By

from logic.entities import Chapter
from logic.websites import Website
from logic.websites.normal_website import NormalWebsite
from utils import image, selenium


class LightNovelCave(NormalWebsite):
    def __init__(self, driver: webdriver.Chrome):
        selectors = {
            '_get_title': '#novel > header > div.header-body.container > div.novel-info > div.main-head > h1',
            '_get_description': '#info > div.summary > div',
            '_get_author': '#novel > header > div.header-body.container > div.novel-info > div.main-head > div.author > a > span',
            '_get_cover_img': '#novel > header > div.header-body.container > div.fixed-img > figure > img',
            'get_table_content_element': '#novel > div > nav > a.grdbtn.chapter-latest-container',
            'get_chapter_list': '#chpagedlist > ul',
            'get_chapter_content': '#chapter-container',
        }
        super().__init__(driver, Website.LightNovelCave, selectors)

    def _get_cover_img(self, novel_title):
        img_src = self._get_image_src(self.selectors['_get_cover_img'])

        return image.download_with_screenshot(self.driver, novel_title, img_src) if img_src else None

    def get_chapters_from_page(self) -> [Chapter]:
        return super().get_chapter_list()

    def get_chapter_list(self) -> [Chapter]:
        all_chapters = []
        while True:
            all_chapters.extend(self.get_chapters_from_page())

            next_page = selenium.get_element(
                self.driver,
                By.CSS_SELECTOR,
                '#chpagedlist > div > div > div > ul > li.PagedList-skipToNext > a'
            )
            if next_page:
                selenium.wait_and_click(self.driver, next_page)
                time.sleep(0.3)
            else:
                break
        return all_chapters
