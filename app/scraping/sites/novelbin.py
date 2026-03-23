from __future__ import annotations

from app.scraping.base import SelectorCandidate
from app.scraping.sites.normal_site import NormalSite


class NovelBinSite(NormalSite):
    def __init__(self, browser):
        selectors = {
            '_get_title': '#novel > div.col-xs-12.col-sm-12.col-md-9.col-novel-main > div.col-xs-12.col-info-desc > div.col-xs-12.col-sm-8.col-md-8.desc > h3',
            '_get_description': '#tab-description > div',
            '_get_author': [
                '#novel > div.col-xs-12.col-sm-12.col-md-9.col-novel-main > div.col-xs-12.col-info-desc > div.col-xs-12.col-sm-8.col-md-8.desc > ul > li:nth-child(1) > a',
                '#novel > div.col-xs-12.col-sm-12.col-md-9.col-novel-main > div.col-xs-12.col-info-desc > div.col-xs-12.col-sm-8.col-md-8.desc > ul > li:nth-child(2) > a',
            ],
            '_get_cover_img': SelectorCandidate(
                css='#novel > div.col-xs-12.col-sm-12.col-md-9.col-novel-main > div.col-xs-12.col-info-desc > div.col-xs-12.col-sm-4.col-md-4.info-holder.csstransforms3d > div > div.book > img',
                attr='src',
                required=False,
            ),
            'get_table_content_clickable_element': '#tab-chapters-title',
            'get_chapter_list': '#list-chapter > div > div > div > div > div > ul > li',
            'get_chapter_content': '#chr-content',
        }
        super().__init__(browser, "NovelBin", selectors)


    def get_loading_delay(self) -> float:
        return 1.9
