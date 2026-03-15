from app.core.export import NovelExporter
from app.core.service import NovelService
from app.scraping.browser import SeleniumBrowser
from app.storage.file_db import FileDB
from app.ui.app import NovelApp


def build_app(use_undetected: bool = True, is_chromium: bool = False) -> NovelApp:
    db = FileDB()
    browser = SeleniumBrowser(db=db, use_undetected_driver=use_undetected, is_chromium=is_chromium)
    service = NovelService(db=db, browser=browser, exporter=NovelExporter())
    return NovelApp(service)


def main() -> None:
    app = build_app(use_undetected=True, is_chromium=False)
    app.run()


if __name__ == "__main__":
    main()
