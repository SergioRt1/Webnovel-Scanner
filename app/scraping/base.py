from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from app.models.entities import Chapter, Novel
from app.utils import selenium_utils
from app.utils.image_utils import download_image


@dataclass(frozen=True)
class SelectorCandidate:
    css: str
    attr: str | None = None
    required: bool = True
    strip: bool = True


def _to_candidates(raw: str | SelectorCandidate | Iterable[str | SelectorCandidate]) -> list[SelectorCandidate]:
    if isinstance(raw, str):
        return [SelectorCandidate(css=raw)]
    if isinstance(raw, SelectorCandidate):
        return [raw]

    result: list[SelectorCandidate] = []
    for item in raw:
        if isinstance(item, str):
            result.append(SelectorCandidate(css=item))
        else:
            result.append(item)
    return result


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
    selectors: dict[str, list[SelectorCandidate]]

    def __init__(self, browser, website_id: str, selectors: dict[str, str | SelectorCandidate | Iterable[str | SelectorCandidate]]):
        super().__init__(browser, website_id)
        self.selectors = {key: _to_candidates(value) for key, value in selectors.items()}

    def _find_first_working_candidate(
        self,
        key: str,
        *,
        timeout: int = 8,
    ) -> tuple[SelectorCandidate, WebElement]:
        candidates = self.selectors.get(key, [])
        if not candidates:
            raise KeyError(f"Missing selector configuration for '{key}' in {self.website_id}")

        last_error: Exception | None = None

        for candidate in candidates:
            if not candidate.css:
                continue
            try:
                element = selenium_utils.wait_for(self.browser.driver, By.CSS_SELECTOR, candidate.css, timeout)
                return candidate, element
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as exc:
                last_error = exc
                continue

        raise ValueError(
            f"No selector matched for '{key}' in {self.website_id}. "
            f"Tried: {[c.css for c in candidates]}"
        ) from last_error

    def _get_value(self, key: str, *, timeout: int = 8, allow_empty: bool = False) -> str:
        candidates = self.selectors.get(key, [])
        if not candidates:
            raise KeyError(f"Missing selector configuration for '{key}' in {self.website_id}")

        last_error: Exception | None = None
        # novel > div.col-xs-12.col-sm-12.col-md-9.col-novel-main > div.col-xs-12.col-info-desc > div.col-xs-12.col-sm-4.col-md-4.info-holder.csstransforms3d > div > div.book > img
        for candidate in candidates:
            if not candidate.css:
                continue
            try:
                element = selenium_utils.wait_for(self.browser.driver, By.CSS_SELECTOR, candidate.css, timeout)

                if candidate.attr:
                    value = element.get_attribute(candidate.attr) or ""
                else:
                    value = element.text or ""

                if candidate.strip:
                    value = value.strip()

                if value or allow_empty or not candidate.required:
                    return value
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as exc:
                last_error = exc
                continue

        raise ValueError(
            f"No valid value found for '{key}' in {self.website_id}. "
            f"Tried: {[c.css for c in candidates]}"
        ) from last_error

    def _get_optional_value(self, key: str, *, timeout: int = 5, default: str = "") -> str:
        try:
            return self._get_value(key, timeout=timeout, allow_empty=True)
        except Exception:
            return default

    def _get_cover_img(self, novel_title: str) -> str | None:
        src = self._get_optional_value("_get_cover_img", timeout=5, default="")
        if not src:
            return None
        return download_image(src, novel_title)

    def search_novel_metadata(self, novel_url: str) -> Novel | None:
        title = self._get_value("_get_title")
        desc = self._get_optional_value("_get_description")
        author = self._get_optional_value("_get_author", default="Unknown")
        image = self._get_cover_img(title) or ""
        return Novel(
            title=title,
            author=author,
            url=novel_url,
            desc=desc,
            website=self.website_id,
            image=image,
        )

    def get_table_content_element(self) -> WebElement | None:
        try:
            _candidate, element = self._find_first_working_candidate("get_table_content_clickable_element", timeout=4)
            return element
        except Exception:
            return None

    def get_chapter_list(self) -> list[Chapter] | None:
        candidates = self.selectors.get("get_chapter_list", [])
        if not candidates:
            raise KeyError(f"Missing selector configuration for 'get_chapter_list' in {self.website_id}")

        last_error: Exception | None = None

        for candidate in candidates:
            if not candidate.css:
                continue
            try:
                items = selenium_utils.safe_find_all(self.browser.driver, candidate.css, timeout=8)
                chapters: list[Chapter] = []

                for order, item in enumerate(items, start=1):
                    try:
                        link = item if item.tag_name.lower() == "a" else item.find_element(By.TAG_NAME, "a")
                        title = link.text.strip()
                        url = link.get_attribute("href") or ""
                        if title and url:
                            chapters.append(Chapter(title=title, url=url, order=order))
                    except Exception:
                        continue

                if chapters:
                    return chapters
            except Exception as exc:
                last_error = exc
                continue

        raise ValueError(
            f"No chapter list selector worked for {self.website_id}. "
            f"Tried: {[c.css for c in candidates]}"
        ) from last_error

    def get_chapter_content(self) -> str:
        _candidate, content_element = self._find_first_working_candidate('get_chapter_content')
        return '\n'.join(p.text for p in content_element.find_elements(By.TAG_NAME, 'p')).strip()
