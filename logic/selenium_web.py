import random
import time

import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from typing import List

from db.file import SimpleFileDB
from utils import selenium
from .entities import Chapter, Novel
from .websites import Website, BasicWebsite


def get_driver(use_undetected: bool, is_chromium: bool) -> webdriver.Chrome:
    type = ChromeType.GOOGLE
    if is_chromium:
        type = ChromeType.CHROMIUM
    if use_undetected:
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument('--disable-popup-blocking')

        driver_service = ChromeService(ChromeDriverManager(chrome_type=type).install())
        return uc.Chrome(options=options, use_subprocess=False, driver_executable_path=driver_service.path)
    else:
        return webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))


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
    def __init__(self, db: SimpleFileDB, driver: webdriver.Chrome = None, websites: dict[Website, BasicWebsite] = None,
                 use_undetected_driver: bool = False):
        self.websites = websites
        self.driver = driver
        self.use_undetected_driver = use_undetected_driver
        self.db = db

    def scroll_to_end(self) -> None:
        """
        Scrolls to the bottom of the page.
        This is a blocking function.
        """
        delay = random.uniform(1, 2) if self.use_undetected_driver else 0.5
        delta = random.uniform(0.1, 0.3) if self.use_undetected_driver else 0.1
        time.sleep(delay)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(delay + delta)

    def fetch_page(self, url: str, title: str) -> None:
        max_retry = 5
        current = 0
        while current < max_retry:
            try:
                print(f"Loading [{title}] {url}...", end="")
                self.driver.get(url)
                print(" Loaded")
                self.scroll_to_end()
                return
            except Exception as ex:
                current += 1
                print("Error loading Page", ex)
                time.sleep(0.8)
        raise ConnectionError("Error loading page")

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
            self.fetch_page(novel_url, "Searching metadata")
            return website.search_novel_metadata(novel_url)

    def get_chapter_list(self, novel: Novel) -> List[Chapter]:
        website = self.websites.get(novel.website)
        if website:
            return self._get_chapter_list(website)

    def close(self):
        self.driver.close()

    def download_novel(self, novel: Novel):
        website = self.websites.get(novel.website)
        for chapter in novel.get_chapters_to_download():
            self.fetch_page(chapter.url, chapter.title)
            content = website.get_chapter_content()
            if not content:
                continue

            chapter.content = content
            novel.downloaded_set.add(chapter.title)

            self.db.set_chapter(novel, chapter)
