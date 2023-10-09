from abc import ABC, abstractmethod
from enum import Enum

from selenium import webdriver
from selenium.webdriver.common.by import By

import utils.selenium as selen
from logic.entities import Novel


def get_website_ids() -> list[str]:
    return [website.value for website in Website]


class Website(Enum):
    Webnovel = "https://www.webnovel.com"
    LightNovelCave = "https://www.lightnovelcave.com"
    NovelCool = "https://www.novelcool.com"


class BasicWebsite(ABC):
    def __init__(self, driver: webdriver.Chrome, website_id: Website):
        self.driver = driver
        self.id = website_id

    def _get_element_text(self, css_selector: str) -> str | None:
        element = selen.get_element(self.driver, By.CSS_SELECTOR, css_selector)
        if element:
            text = element.text
            if not text:
                text = element.get_attribute("innerText")
            return text

        return None

    def _get_image_src(self, css_selector: str) -> str | None:
        img = selen.get_element(self.driver, By.CSS_SELECTOR, css_selector)
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
