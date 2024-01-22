from selenium import webdriver

from logic.entities import Chapter
from logic.websites import Website
from logic.websites.normal_website import NormalWebsite


class NovelCool(NormalWebsite):
    def __init__(self, driver: webdriver.Chrome):
        selectors = {
            '_get_title': 'body > div.site-content > div.bookinfo-module > div.bk-intro > div.bk-side-intro > div.bk-side-intro-most > h1',
            '_get_description': 'body > div.site-content > div.bookinfo-module > div.for-mob > div.bk-summary > div.bk-summary-txt',
            '_get_author': 'body > div.site-content > div.bookinfo-module > div.bk-intro > div.bk-side-intro > div.bk-side-intro-most > div.bookinfo-author > a > span',
            '_get_cover_img': 'body > div.site-content > div.bookinfo-module > div.bk-intro > div.bookinfo-pic > a > img',
            'get_table_content_clickable_element': 'body > div.site-content > section > div > div.tab-item.active > div.bookwarn-module > div > div.bookwarn-continue.text-underline.pointer.toggle-trigger',
            'get_chapter_list': 'body > div.site-content > section > div > div.tab-item.active > div:nth-child(2) > div.chapter-item-list > div',
            'get_chapter_content': 'body > div.site-content > div.chp-skin.null > div.chapter-reading-section-list > div > div',
        }
        super().__init__(driver, Website.NovelCool, selectors)

    def get_chapter_list(self) -> [Chapter]:
        return list(reversed(super().get_chapter_list()))
