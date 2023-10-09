from db.file import SimpleFileDB
from logic.novel_downloader import NovelDownloader
from logic.selenium_web import ScrapperSelenium, get_driver
from logic.websites import Website
from logic.websites.lightnovelcave import LightNovelCave
from logic.websites.novelcool import NovelCool
from logic.websites.webnovel import WebNovel
from ui import NovelUI


def build_app(use_undetected, max_per_volume):
    db = SimpleFileDB()

    driver = get_driver(use_undetected)
    driver.stop_client()
    websites = {
        Website.Webnovel: WebNovel(driver),
        Website.LightNovelCave: LightNovelCave(driver),
        Website.NovelCool: NovelCool(driver),
    }
    scrapper = ScrapperSelenium(db, driver, websites, use_undetected)
    downloader = NovelDownloader(db, scrapper, max_per_volume)

    app = NovelUI(downloader)
    driver.start_client()

    return app
