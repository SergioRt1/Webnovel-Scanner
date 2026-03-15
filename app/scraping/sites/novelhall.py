from __future__ import annotations

import re

from app.scraping.sites.normal_site import NormalSite


class NovelHallSite(NormalSite):
    def __init__(self, browser):
        selectors = {
            '_get_title': '#main > div > div.book-main.inner.mt30 > div.book-info > h1',
            '_get_description': '#main > div > div.book-main.inner.mt30 > div.book-info > div.intro > span.js-close-wrap',
            '_get_author': '#main > div > div.book-main.inner.mt30 > div.book-info > div.total.booktag > span:nth-child(2)',
            '_get_cover_img': '#main > div > div.book-main.inner.mt30 > div.book-img.hidden-xs > img',
            'get_table_content_clickable_element': '',
            'get_chapter_list': '#morelist',
            'get_chapter_content': '#htmlContent',
        }
        super().__init__(browser, "NovelHall", selectors)

    def get_loading_delay(self) -> float:
        return 1.9

    def get_chapter_content(self) -> str:
        return re.sub(r"\n+", "\n", super().get_chapter_content().strip())
