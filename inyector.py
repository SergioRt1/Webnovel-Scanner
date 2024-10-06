from db.file import SimpleFileDB
from logic.filter import ContentFilter
from logic.novel_downloader import NovelDownloader
from logic.selenium_web import ScrapperSelenium, get_driver
from logic.websites import Website
from logic.websites.lightnovelcave import LightNovelCave
from logic.websites.novel_bin import NovelBin
from logic.websites.novelcool import NovelCool
from logic.websites.webnovel import WebNovel
from ui import NovelUI


def build_app(use_undetected, max_per_volume):
    db = SimpleFileDB()

    driver = get_driver(use_undetected)
    driver.stop_client()
    websites = {
        Website.Webnovel: WebNovel(driver),
        Website.NovelBin: NovelBin(driver),
        Website.LightNovelCave: LightNovelCave(driver),
        Website.NovelCool: NovelCool(driver),
    }
    scrapper = ScrapperSelenium(db, driver, websites, use_undetected)
    downloader = NovelDownloader(db, scrapper, max_per_volume)
    filter = ContentFilter()

    app = NovelUI(downloader, filter)
    driver.start_client()

    return app
