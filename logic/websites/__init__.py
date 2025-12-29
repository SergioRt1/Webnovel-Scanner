from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

from selenium.webdriver.common.by import By

import utils.selenium as selen
from logic.entities import Novel

if TYPE_CHECKING:
    from logic.selenium_web import ScrapperSelenium

def get_website_ids() -> list[str]:
    return [website.value for website in Website]


class Website(Enum):
    NovelBin = "https://novel-bin.com"
    Webnovel = "https://www.webnovel.com"
    NovelCool = "https://www.novelcool.com"
    LightNovelCave = "https://www.lightnovelcave.com"
    NovelHall = "https://www.novelhall.com"

def register_websites(scrapper: ScrapperSelenium) -> None:
    ## By calling the Constructor of a Website, the website will be self register in the scrapper
    from .lightnovelcave import LightNovelCave
    from .novel_bin import NovelBin
    from .novelcool import NovelCool
    from .novelhall import NovelHall
    from .webnovel import WebNovel

    LightNovelCave(scrapper)
    NovelBin(scrapper)
    NovelCool(scrapper)
    NovelHall(scrapper)
    WebNovel(scrapper)

class BasicWebsite(ABC):
    def __init__(self, scrapper: ScrapperSelenium, website_id: Website):
        self.scrapper = scrapper
        self.id = website_id
        self.scrapper.register_website(self.id, self)

    def _get_element_text(self, css_selector: str) -> str | None:
        element = selen.get_element(self.scrapper.driver, By.CSS_SELECTOR, css_selector)
        if element:
            text = element.text
            if not text:
                text = element.get_attribute("innerText")
            return text

        return None

    def _get_image_src(self, css_selector: str) -> str | None:
        img = selen.get_element(self.scrapper.driver, By.CSS_SELECTOR, css_selector)
        return img.get_attribute('src') if img else None

    @abstractmethod
    def _get_title(self):
        pass

    @abstractmethod
    def _get_description(self):
        pass

    @abstractmethod
    def _get_author(self):
        pass

    @abstractmethod
    def _get_cover_img(self, novel_title):
        pass

    @abstractmethod
    def _get_chapter_title(self, a):
        pass

    def get_loading_delay(self) -> float:
        return 1

    def search_novel_metadata(self, novel_url):
        novel_title = self._get_title()
        return Novel(
            novel_title,
            self._get_author(),
            novel_url,
            self._get_description(),
            self.id,
            self._get_cover_img(novel_title)
        )

    @abstractmethod
    def get_table_content_element(self):
        pass

    @abstractmethod
    def get_chapter_list(self):
        pass

    @abstractmethod
    def get_chapter_content(self):
        pass
