from __future__ import annotations

import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

from app.models.entities import Chapter
from app.scraping.base import SelectorCandidate
from app.scraping.sites.normal_site import NormalSite
from app.utils import selenium_utils


class FreeWebNovelSite(NormalSite):
    def __init__(self, browser):
        selectors = {
            "_get_title": ".m-desc h1.tit",
            "_get_description": ".m-desc .txt .inner",
            "_get_author": [
                "a[href*='/author/']",
                ".m-imgtxt .txt .item a",
            ],
            "_get_cover_img": SelectorCandidate(
                css=".m-imgtxt .pic img",
                attr="src",
                required=False,
            ),
            "get_table_content_clickable_element": "",
            "get_chapter_list": "#idData li",
            "get_chapter_content": [
                "#article",
                ".m-read",
            ],
        }
        super().__init__(browser, "FreeWebNovel", selectors)

    def get_chapter_list(self) -> list[Chapter] | None:
        driver = self.browser.driver
        chapters: list[Chapter] = []

        while True:
            try:
                # Wait for the elements to be present using a short timeout.
                items = selenium_utils.safe_find_all(driver, "#idData li", timeout=8)
            except Exception as exc:
                if not chapters:
                    raise exc
                break

            page_chapters_added = 0
            for item in items:
                try:
                    link = item if item.tag_name.lower() == "a" else item.find_element(By.TAG_NAME, "a")
                    title = link.text.strip()
                    url = link.get_attribute("href") or ""
                    if title and url:
                        order = len(chapters) + 1
                        chapters.append(Chapter(title=title, url=url, order=order))
                        page_chapters_added += 1
                except Exception:
                    continue

            if page_chapters_added == 0:
                break

            # Try to find the next button using selector/id `#nextBtn`
            try:
                next_btn = driver.find_element(By.ID, "nextBtn")

                # Check if it has "None" text or "none" class
                btn_text = next_btn.text.strip().lower()
                btn_class = next_btn.get_attribute("class") or ""

                if btn_text == "none" or "none" in btn_class.split():
                    break

                # Record the last chapter's url on this page to detect when it updates
                last_chapter_href = chapters[-1].url if chapters else ""

                # Click the next page button. Using JS click is extremely reliable.
                driver.execute_script("arguments[0].click();", next_btn)

                # Wait for the page content to update (i.e. the last chapter on the page changes)
                updated = False
                for _ in range(50):  # Wait up to 5 seconds
                    time.sleep(0.1)
                    try:
                        new_items = driver.find_elements(By.CSS_SELECTOR, "#idData li")
                        if new_items:
                            new_link = new_items[-1] if new_items[-1].tag_name.lower() == "a" else new_items[-1].find_element(By.TAG_NAME, "a")
                            new_href = new_link.get_attribute("href") or ""
                            if new_href != last_chapter_href:
                                updated = True
                                break
                    except (NoSuchElementException, StaleElementReferenceException):
                        continue

                if not updated:
                    # Timeout waiting for page to update, break to avoid infinite loop
                    break

            except NoSuchElementException:
                break
            except Exception:
                break

        return chapters
