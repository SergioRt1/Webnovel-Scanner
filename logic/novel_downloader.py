from db.file import SimpleFileDB
from .entities import Novel
from .selenium_web import ScrapperSelenium


class NovelDownloader:
    def __init__(self, db: SimpleFileDB, scrapper: ScrapperSelenium, max_per_volume):
        self.scrapper = scrapper
        self.max_per_volume = max_per_volume
        self.db = db

        self.novels = self._get_all_novels()

    def search_novel(self, novel_url, website_name: str) -> [Novel]:
        novel = self.scrapper.search_basic_novel_info(novel_url, website_name)
        novel.chapter_list = self.scrapper.get_chapter_list(novel)

        self.db.save_novel(novel)

        return [novel] if novel else []

    def sync_novels(self):
        self.novels = self._get_all_novels()

    def _get_all_novels(self) -> [Novel]:
        return sorted(self.db.get_all(), key=lambda novel: novel.title)

    def download_novel(self, novel: Novel):
        try:
            self.scrapper.download_novel(novel)
            return True
        except ConnectionError:
            return False
        finally:
            print("============== SAVING NOVEL ==============")
            self.db.save_novel(novel)

    def delete_novel(self, novel):
        return self.db.delete_novel(novel.title)

    def write_novel(self, novel: Novel):
        novel.write_to_txt(self.max_per_volume)

    def get_downloaded_novels(self):
        return set(novel.title for novel in self.novels if novel.is_downloaded())
