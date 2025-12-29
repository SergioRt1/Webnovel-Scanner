import random
import time

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from typing import List, Optional
from tqdm import tqdm

from db.file import SimpleFileDB
from utils import selenium
from .entities import Chapter, Novel
from .websites import Website, BasicWebsite, register_websites


def get_driver(use_undetected: bool, is_chromium: bool) -> webdriver.Chrome:
    type = ChromeType.GOOGLE

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument('--disable-popup-blocking')
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    if is_chromium:
        type = ChromeType.CHROMIUM
    if use_undetected:
        driver_service = ChromeService(ChromeDriverManager(chrome_type=type).install())
        return uc.Chrome(options=options, use_subprocess=False, driver_executable_path=driver_service.path)
    else:
        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)


def _fix_duplicates(chapter_list: List[Chapter]) -> List[Chapter]:
    titles = set()
    duplicated_titles = {}

    for chapter in chapter_list:
        if chapter.title in titles:
            if chapter.title in duplicated_titles:
                duplicated_titles[chapter.title].append(chapter)
            else:
                duplicated_titles[chapter.title] = [chapter]
        else:
            titles.add(chapter.title)

    for title in duplicated_titles:
        count = 1
        for chapter in duplicated_titles[title]:
            chapter.title += f' ({count})'
            count += 1

    return chapter_list


class ScrapperSelenium:
    def __init__(
            self,
            db: SimpleFileDB,
            use_undetected_driver: bool = False,
            driver_factory=lambda: get_driver(use_undetected=True, is_chromium=False),
            restart_every_pages: Optional[int] = 350,
    ):
        self.use_undetected_driver = use_undetected_driver
        self.db = db
        self.driver_factory = driver_factory
        self.driver = self.driver_factory()
        self.restart_every_pages = restart_every_pages
        self._pages_loaded = 0

        self._apply_driver_settings()
        self.websites = dict()
        register_websites(self)

    def _apply_driver_settings(self) -> None:
        self.driver.set_page_load_timeout(10) # Timeout for driver.get()
        self.driver.set_script_timeout(10) # Timeout for async JS execution

    def _restart_driver(self):
        print("Restating driver")
        self.quit()

        self.driver = self.driver_factory()
        self._apply_driver_settings()

    def _recover_tab(self) -> None:
        """
        Replaces the current tab with a fresh one *within the same browser*.
        This often recovers from renderer/tab weird states while preserving cookies/session.
        """
        try:
            print("Reopening in a new tab.")
            old_handle = self.driver.current_window_handle
            self.driver.switch_to.new_window("tab")
            new_handle = self.driver.current_window_handle

            # Close the old tab
            try:
                self.driver.switch_to.window(old_handle)
                self.driver.close()
            except Exception:
                pass

            # Switch back to the new tab
            self.driver.switch_to.window(new_handle)
        except Exception:
            # If tab recovery fails, fall back to full restart
            self._restart_driver()

    def register_website(self, key: Website, website: BasicWebsite):
        self.websites[key] = website

    def scroll_to_end(self, load_delay: float = 1) -> None:
        """
        Scrolls to the bottom of the page.
        This is a blocking function.
        """
        delay = random.uniform(load_delay, load_delay+0.5) if self.use_undetected_driver else load_delay
        delta = random.uniform(0.1, 0.3) if self.use_undetected_driver else 0.1
        time.sleep(delay)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(delay + delta)


    def fetch_page(
            self,
            url: str,
            load_delay: float = 1,
            max_retry: int = 5,
    ) -> None:
        self._pages_loaded += 1
        if self.restart_every_pages and (self._pages_loaded % self.restart_every_pages == 0):
            self._restart_driver()

        for attempt in range(1, max_retry + 1):
            try:
                self.driver.get(url)
                self.scroll_to_end(load_delay)
                return
            except TimeoutException as ex:
                try:
                    print(f"Timeout ({attempt}/{max_retry}): {ex}")
                    self.driver.execute_script("window.stop();")
                except Exception:
                    pass
                self._recover_tab()

            except Exception as ex:
                print(f"Driver exception ({attempt}/{max_retry}): {ex}")
                # Escalate: tab first, then full restart if it repeats
                if attempt <= 2:
                    self._recover_tab()
                else:
                    self._restart_driver()

            # jittered backoff between retries
            backoff = min(8.0, (0.75 * attempt) + random.uniform(0, 0.5))
            time.sleep(backoff)

        raise ConnectionError(f"Error loading page after {max_retry} attempts: {url}")

    def _get_chapter_list(self, website):
        table_contents = website.get_table_content_element()
        if table_contents:
            selenium.wait_and_click(self.driver, table_contents)

        self.scroll_to_end()

        chapter_list = website.get_chapter_list()

        chapter_list = _fix_duplicates(chapter_list)

        return chapter_list

    def search_basic_novel_info(self, novel_url: str, website_name) -> Novel | None:
        website = self.websites.get(Website(website_name))
        if website:
            self.fetch_page(novel_url)
            return website.search_novel_metadata(novel_url)

    def get_chapter_list(self, novel: Novel) -> List[Chapter] | None:
        website = self.websites.get(novel.website)
        if website:
            return self._get_chapter_list(website)

    def quit(self):
        try:
            self.driver.quit()
        except Exception as ex:
            print("Error quiting driver: ", ex)

    def download_novel(self, novel: Novel):
        website = self.websites.get(novel.website)
        chapters = novel.get_chapters_to_download()

        with tqdm(chapters, desc="Loading") as pbar:
            for chapter in pbar:
                pbar.set_postfix_str(f"{chapter.title}: {chapter.url}")
                self.fetch_page(chapter.url, website.get_loading_delay())
                content = website.get_chapter_content()
                if not content:
                    continue

                chapter.content = content
                novel.downloaded_set.add(chapter.title)

                self.db.set_chapter(novel, chapter)
