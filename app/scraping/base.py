from __future__ import annotations

from abc import ABC, abstractmethod

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from app.models.entities import Chapter, Novel
from app.utils import selenium_utils
from app.utils.image_utils import download_image


class BaseWebsite(ABC):
    def __init__(self, browser, website_id: str):
        self.browser = browser
        self.website_id = website_id

    @abstractmethod
    def search_novel_metadata(self, novel_url: str) -> Novel | None:
        raise NotImplementedError

    @abstractmethod
    def get_chapter_list(self) -> list[Chapter] | None:
        raise NotImplementedError

    @abstractmethod
    def get_chapter_content(self) -> str:
        raise NotImplementedError

    def get_loading_delay(self) -> float:
        return 1.0

    def get_table_content_element(self) -> WebElement | None:
        return None


class SelectorWebsite(BaseWebsite):
    selectors: dict[str, str]

    def __init__(self, browser, website_id: str, selectors: dict[str, str]):
        super().__init__(browser, website_id)
        self.selectors = selectors

    def _get_text(self, key: str) -> str:
        return selenium_utils.safe_get_text(self.browser.driver, self.selectors[key])

    def _get_attribute(self, key: str, attribute: str) -> str | None:
        return selenium_utils.safe_get_attribute(self.browser.driver, self.selectors[key], attribute)

    def _get_cover_img(self, novel_title: str) -> str | None:
        src = self._get_attribute("_get_cover_img", "src")
        if not src:
            return None
        return download_image(src, novel_title)

    def search_novel_metadata(self, novel_url: str) -> Novel | None:
        title = self._get_text("_get_title")
        desc = self._get_text("_get_description")
        author = self._get_text("_get_author")
        image = self._get_cover_img(title) or ""
        return Novel(title=title, author=author, url=novel_url, desc=desc, website=self.website_id, image=image)

    def get_table_content_element(self) -> WebElement | None:
        selector = self.selectors.get("get_table_content_clickable_element")
        if not selector:
            return None
        try:
            return selenium_utils.wait_for(self.browser.driver, By.CSS_SELECTOR, selector)
        except Exception:
            return None

    def get_chapter_list(self) -> list[Chapter] | None:
        items = selenium_utils.safe_find_all(self.browser.driver, self.selectors["get_chapter_list"])
        chapters: list[Chapter] = []
        for order, item in enumerate(items, start=1):
            link = item.find_element(By.TAG_NAME, "a")
            title = link.text.strip()
            url = link.get_attribute("href")
            if title and url:
                chapters.append(Chapter(title=title, url=url, order=order))
        return chapters

    def get_chapter_content(self) -> str:
        chapter_content = selenium_utils.safe_find(self.browser.driver, self.selectors['get_chapter_content'])
        return '\n'.join(p.text for p in chapter_content.find_elements(By.TAG_NAME, 'p')).strip()
