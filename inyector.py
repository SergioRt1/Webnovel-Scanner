from db.file import SimpleFileDB
from logic.filters.lsh_filter import ContentFilterLSH
from logic.novel_downloader import NovelDownloader
from logic.selenium_web import ScrapperSelenium

from ui import NovelUI


def build_app(use_undetected, max_per_volume, is_chromium):
    db = SimpleFileDB()

    scrapper = ScrapperSelenium(db, use_undetected)
    downloader = NovelDownloader(db, scrapper, max_per_volume)
    content_filter = ContentFilterLSH()

    app = NovelUI(downloader, content_filter)
    scrapper.driver.start_client()

    return app
