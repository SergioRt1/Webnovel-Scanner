from selenium import webdriver

from logic.websites import Website
from logic.websites.normal_website import NormalWebsite
from utils import image


class NovelBin(NormalWebsite):
    def __init__(self, driver: webdriver.Chrome):
        selectors = {
            '_get_title': '#novel > div.col-xs-12.col-sm-12.col-md-9.col-novel-main > div.col-xs-12.col-info-desc > div.col-xs-12.col-sm-8.col-md-8.desc > h3',
            '_get_description': '#tab-description > div',
            '_get_author': '#novel > div.col-xs-12.col-sm-12.col-md-9.col-novel-main > div.col-xs-12.col-info-desc > div.col-xs-12.col-sm-8.col-md-8.desc > ul > li:nth-child(2) > a',
            '_get_cover_img': '#novel > div.col-xs-12.col-sm-12.col-md-9.col-novel-main > div.col-xs-12.col-info-desc > div.col-xs-12.col-sm-4.col-md-4.info-holder.csstransforms3d > div > div.book > img',
            'get_table_content_clickable_element': '#tab-chapters-title',
            'get_chapter_list': '#list-chapter > div > div > div',
            'get_chapter_content': '#chr-content',
        }
        super().__init__(driver, Website.NovelBin, selectors)

    def _get_cover_img(self, novel_title):
        img_src = self._get_image_src(self.selectors['_get_cover_img'])

        return image.download_with_screenshot(self.driver, novel_title, img_src) if img_src else None
