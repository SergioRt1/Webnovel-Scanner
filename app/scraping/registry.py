from __future__ import annotations

from app.scraping.sites.novelbin import NovelBinSite
from app.scraping.sites.novelcool import NovelCoolSite
from app.scraping.sites.novelhall import NovelHallSite
from app.scraping.sites.webnovel import WebNovelSite


def register_websites(browser) -> None:
    # This is the order in the dropdown
    browser.register_website("NovelBin", NovelBinSite(browser))
    browser.register_website("NovelHall", NovelHallSite(browser))
    browser.register_website("NovelCool", NovelCoolSite(browser))
    browser.register_website("WebNovel", WebNovelSite(browser))
