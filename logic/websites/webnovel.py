from selenium import webdriver

from logic.websites import Website
from logic.websites.normal_website import NormalWebsite


class WebNovel(NormalWebsite):
    def __init__(self, driver: webdriver.Chrome):
        selectors = {
            '_get_title': 'body > div.page > div.det-hd.mb48 > div > div > div._mn.g_col._8.pr > h1',
            '_get_description': '#about > div.g_wrap.det-abt.mb48 > div.g_txt_over.mb48.fs16.j_synopsis._txtover > p',
            '_get_author': 'body > div.page > div.det-hd.mb48 > div > div > div._mn.g_col._8.pr > address > h2 > a',
            '_get_cover_img': 'body > div.page > div.det-hd.mb48 > div > div > div._sd.g_col._4 > i > img:nth-child(1)',
            'get_table_content_clickable_element': 'body > div.page > div.g_wrap.det-tab-nav.mb48._slide > a.j_show_contents',
            'get_chapter_list': '#contents > div > div.fs16.det-con-ol.oh.j_catalog_list',
            'get_chapter_content': '#page > div.cha-page-in > div.j_contentWrap > div > div.cha-content',
        }
        super().__init__(driver, Website.Webnovel, selectors)
