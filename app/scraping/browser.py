from __future__ import annotations

import random
import time
from typing import Optional

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from app.config import DEFAULT_RESTART_EVERY_PAGES
from app.core.cancel import EventToken, NoopToken
from app.models.entities import Novel
from app.storage.file_db import FileDB
from app.utils import selenium_utils
from app.scraping.registry import register_websites


def build_driver(use_undetected: bool, is_chromium: bool) -> webdriver.Chrome:
    chrome_type = ChromeType.CHROMIUM if is_chromium else ChromeType.GOOGLE
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    if use_undetected:
        driver_service = ChromeService(ChromeDriverManager(chrome_type=chrome_type).install())
        return uc.Chrome(options=options, use_subprocess=False, driver_executable_path=driver_service.path)

    return webdriver.Chrome(service=ChromeService(ChromeDriverManager(chrome_type=chrome_type).install()), options=options)


class SeleniumBrowser:
    def __init__(
        self,
        db: FileDB,
        use_undetected_driver: bool = True,
        is_chromium: bool = False,
        restart_every_pages: Optional[int] = DEFAULT_RESTART_EVERY_PAGES,
        driver_factory=None,
    ):
        self.db = db
        self.use_undetected_driver = use_undetected_driver
        self.restart_every_pages = restart_every_pages
        self.driver_factory = driver_factory or (
            lambda: build_driver(use_undetected=use_undetected_driver, is_chromium=is_chromium)
        )
        self.driver = self.driver_factory()
        self._pages_loaded = 0
        self.websites: dict[str, object] = {}
        self._apply_driver_settings()
        register_websites(self)

    def _apply_driver_settings(self) -> None:
        self.driver.set_page_load_timeout(15)
        self.driver.set_script_timeout(15)

    def register_website(self, key: str, website) -> None:
        self.websites[key] = website

    def get_registered_websites(self):
        return list(self.websites)

    def _restart_driver(self) -> None:
        self.quit()
        self.driver = self.driver_factory()
        self._apply_driver_settings()

    def _recover_tab(self) -> None:
        try:
            old_handle = self.driver.current_window_handle
            self.driver.switch_to.new_window("tab")
            new_handle = self.driver.current_window_handle
            self.driver.switch_to.window(old_handle)
            self.driver.close()
            self.driver.switch_to.window(new_handle)
        except Exception:
            self._restart_driver()

    def scroll_to_end(self, load_delay: float = 1.0, cancel_token: EventToken = NoopToken()) -> None:
        cancel_token.raise_if_cancelled()
        delay = random.uniform(load_delay, load_delay + 0.5) if self.use_undetected_driver else load_delay
        time.sleep(delay)
        cancel_token.raise_if_cancelled()
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(delay + 0.15)
        cancel_token.raise_if_cancelled()

    def fetch_page(self, url: str, load_delay: float = 1.0, max_retry: int = 5, cancel_token: EventToken = NoopToken()) -> None:
        cancel_token.raise_if_cancelled()

        self._pages_loaded += 1
        if self.restart_every_pages and self._pages_loaded % self.restart_every_pages == 0:
            self._restart_driver()

        for attempt in range(1, max_retry + 1):
            cancel_token.raise_if_cancelled()
            try:
                self.driver.get(url)
                self.scroll_to_end(load_delay, cancel_token=cancel_token)
                return
            except TimeoutException:
                selenium_utils.stop_loading(self.driver)
                self._recover_tab()
            except Exception:
                if attempt <= 2:
                    self._recover_tab()
                else:
                    self._restart_driver()
            time.sleep(min(8.0, 0.75 * attempt + random.uniform(0, 0.5)))

        raise ConnectionError(f"No fue posible cargar la página: {url}")

    def search_basic_novel_info(self, novel_url: str, website_name: str, cancel_token: EventToken) -> Novel | None:
        website = self.websites.get(website_name)
        if not website:
            return None
        self.fetch_page(novel_url, website.get_loading_delay(), cancel_token=cancel_token)
        return website.search_novel_metadata(novel_url)

    def get_chapter_list(self, novel: Novel, cancel_token: EventToken):
        website = self.websites.get(novel.website)
        if not website:
            return []
        cancel_token.raise_if_cancelled()
        table = website.get_table_content_element()
        if table is not None:
            try:
                selenium_utils.wait_and_click(self.driver, table)
            except Exception:
                pass
        self.scroll_to_end(website.get_loading_delay(), cancel_token=cancel_token)
        chapters = website.get_chapter_list() or []
        return self._fix_duplicates(chapters)

    def download_novel(self, novel: Novel, progress_callback, cancel_token: EventToken) -> Novel:
        website = self.websites.get(novel.website)
        if not website:
            raise ValueError(f"Website not registered: {novel.website}")

        chapters = novel.get_chapters_to_download()
        total = len(chapters)
        for index, chapter in enumerate(chapters, start=1):
            cancel_token.raise_if_cancelled()
            if progress_callback:
                progress_callback(index, total, f"Downloading {chapter.title}")
            self.fetch_page(chapter.url, website.get_loading_delay(), cancel_token=cancel_token)
            cancel_token.raise_if_cancelled()
            content = website.get_chapter_content().strip()
            if not content:
                continue
            chapter.content = content
            self.db.set_chapter(novel, chapter)
        return novel

    @staticmethod
    def _fix_duplicates(chapter_list):
        titles = set()
        duplicates: dict[str, int] = {}
        for chapter in chapter_list:
            if chapter.title in titles:
                duplicates[chapter.title] = duplicates.get(chapter.title, 0) + 1
                chapter.title = f"{chapter.title} ({duplicates[chapter.title]})"
            else:
                titles.add(chapter.title)
        return chapter_list

    def quit(self) -> None:
        try:
            self.driver.quit()
        except Exception:
            pass
