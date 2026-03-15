from __future__ import annotations

from app.scraping.sites.normal_site import NormalSite


class WebNovelSite(NormalSite):
    def __init__(self, browser):
        selectors = {
            "_get_title": ".book-info h1",
            "_get_description": ".book-intro",
            "_get_author": ".author-name",
            "_get_cover_img": ".book-img img",
            "get_table_content_clickable_element": "",
            "get_chapter_list": ".cha-content li",
            "get_chapter_content": ".cha-words",
        }
        super().__init__(browser, "WebNovel", selectors)
