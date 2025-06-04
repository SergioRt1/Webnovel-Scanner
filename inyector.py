from db.file import SimpleFileDB
from logic.filters.lsh_filter import ContentFilterLSH
from logic.novel_downloader import NovelDownloader
from logic.selenium_web import ScrapperSelenium, get_driver
from logic.websites import Website
from logic.websites.lightnovelcave import LightNovelCave
from logic.websites.novel_bin import NovelBin
from logic.websites.novelcool import NovelCool
from logic.websites.webnovel import WebNovel
from ui import NovelUI


def build_app(use_undetected, max_per_volume, is_chromium):
    db = SimpleFileDB()

    driver = get_driver(use_undetected, is_chromium)
    driver.set_page_load_timeout(10)  # Timeout for driver.get()
    driver.set_script_timeout(10)     # Timeout for async JS execution

    websites = {
        Website.Webnovel: WebNovel(driver),
        Website.NovelBin: NovelBin(driver),
        Website.LightNovelCave: LightNovelCave(driver),
        Website.NovelCool: NovelCool(driver),
    }
    scrapper = ScrapperSelenium(db, driver, websites, use_undetected)
    downloader = NovelDownloader(db, scrapper, max_per_volume)
    content_filter = ContentFilterLSH()

    app = NovelUI(downloader, content_filter)
    driver.start_client()

    return app
