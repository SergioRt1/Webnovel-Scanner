from __future__ import annotations

from app.core.cancel import EventToken
from app.core.events import ProgressEvent
from app.core.export import NovelExporter
from app.filters.lsh_filter import ContentFilterLSH
from app.ml.integration import MLProcessorAdapter
from app.models.entities import Novel
from app.scraping.browser import SeleniumBrowser
from app.storage.file_db import FileDB


class NovelService:
    def __init__(self, db: FileDB, browser: SeleniumBrowser, exporter: NovelExporter | None = None):
        self.db = db
        self.browser = browser
        self.exporter = exporter or NovelExporter()
        self.duplicate_filter = ContentFilterLSH()
        self.ml = MLProcessorAdapter()

    def get_downloaded_novels(self) -> list[Novel]:
        return self.db.get_all()

    def search_novel(self, novel_url: str, website_name: str, cancel_token: EventToken) -> Novel:
        novel = self.browser.search_basic_novel_info(novel_url, website_name, cancel_token)
        if not novel:
            raise ValueError("No se pudo obtener la metadata de la novela.")
        chapter_list = self.browser.get_chapter_list(novel, cancel_token) or []
        novel.chapter_list = chapter_list
        self.db.save_novel(novel)
        return novel

    def download_novel(self, novel: Novel, progress_callback, cancel_token: EventToken) -> Novel:
        def callback(current: int, total: int, message: str):
            if progress_callback:
                progress_callback(ProgressEvent(message=message, current=current, total=total))

        updated = self.browser.download_novel(novel, callback, cancel_token)
        self.db.save_novel(updated)
        return updated

    def refresh_novel(self, novel: Novel) -> Novel | None:
        saved = self.db.load_novel(novel.safe_title)
        return saved or novel

    def export_novel(self, novel: Novel, max_per_file: int = 300) -> list[str]:
        outputs = []
        outputs.extend(self.exporter.export_txt_split(novel, max_per_file=max_per_file))
        outputs.append(self.exporter.export_single_txt(novel))
        outputs.append(self.exporter.export_metadata(novel))
        return outputs

    def delete_novel(self, novel_title: str) -> bool:
        return self.db.delete_novel(novel_title)

    def ml_is_available(self) -> tuple[bool, str]:
        return self.ml.availability.available, self.ml.availability.error

    def build_ml_training_data(self) -> None:
        self.ml.build_training_data()

    def train_ml_model(self, cancel_token: EventToken) -> None:
        self.ml.train_model(cancel_token)

    def apply_duplicate_filter(self, novel: Novel) -> Novel:
        return self.duplicate_filter.filter_content(novel)

    def run_ml_predictions(self, novel: Novel, progress_callback, cancel_token: EventToken) -> Novel:
        def callback(current: int, total: int, message: str):
            if progress_callback:
                progress_callback(ProgressEvent(message=message, current=current, total=total))
        return self.ml.run_predictions(novel, cancel_token, progress_callback=callback)

    def finalize_ml_cleaning(self, novel: Novel, cancel_token: EventToken) -> Novel:
        cleaned = self.ml.rebuild_chapter_content(novel, cancel_token)
        return cleaned

    def close(self) -> None:
        self.browser.quit()
