from __future__ import annotations

from app.models import Chapter
from app.scraping.sites.normal_site import NormalSite


class NovelCoolSite(NormalSite):
    def __init__(self, browser):
        selectors = {
            '_get_title': 'body > div.site-content > div.bookinfo-module > div.bk-intro > div.bk-side-intro > div.bk-side-intro-most > h1',
            '_get_description': 'body > div.site-content > div.bookinfo-module > div.for-mob > div.bk-summary > div.bk-summary-txt',
            '_get_author': 'body > div.site-content > div.bookinfo-module > div.bk-intro > div.bk-side-intro > div.bk-side-intro-most > div.bookinfo-author > a > span',
            '_get_cover_img': 'body > div.site-content > div.bookinfo-module > div.bk-intro > div.bookinfo-pic > a > img',
            'get_table_content_clickable_element': 'body > div.site-content > section > div > div.tab-item.active > div:nth-child(4) > div:nth-child(3)',
            'get_chapter_list': 'body > div.site-content > section > div > div.tab-item.active > div:nth-child(4) > div.chapter-item-list.all > div',
            'get_chapter_content': 'body > div.site-content > div.chp-skin.null > div.chapter-reading-section-list > div > div',
        }
        super().__init__(browser, "NovelCool", selectors)

    def get_chapter_list(self) -> list[Chapter] | None:
        return list(reversed(super().get_chapter_list()))
