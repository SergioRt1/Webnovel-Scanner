from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd

from app.config import EXPORT_DIR, IMAGE_DIR
from app.utils.files import sanitize_filename


@dataclass
class Chapter:
    title: str
    url: str
    content: str = ""
    order: int = 0
    prediction_df: Optional[pd.DataFrame] = None

    @property
    def is_downloaded(self) -> bool:
        return bool(self.content and self.content.strip())

    @property
    def safe_title(self) -> str:
        return sanitize_filename(self.title)


@dataclass
class Novel:
    title: str
    author: str
    url: str
    desc: str
    website: str
    image: str = ""
    chapter_list: list[Chapter] = field(default_factory=list)
    downloaded_set: set[str] = field(default_factory=set)
    last_error: str = ""

    @property
    def safe_title(self) -> str:
        return sanitize_filename(self.title)

    @property
    def image_path(self) -> str:
        if not self.image:
            return ""
        return str(IMAGE_DIR / self.image)

    @property
    def downloaded_count(self) -> int:
        return len(self.downloaded_set)

    @property
    def total_chapters(self) -> int:
        return len(self.chapter_list)

    @property
    def progress_ratio(self) -> float:
        if self.total_chapters == 0:
            return 0.0
        return self.downloaded_count / self.total_chapters

    @property
    def progress_text(self) -> str:
        return f"{self.downloaded_count}/{self.total_chapters}"

    def get_chapters_to_download(self) -> list[Chapter]:
        return [ch for ch in self.chapter_list if ch.title not in self.downloaded_set]

    def is_downloaded(self) -> bool:
        return self.total_chapters > 0 and self.downloaded_count == self.total_chapters

    def is_new(self) -> bool:
        return self.downloaded_count == 0

    def export_folder(self) -> Path:
        folder = EXPORT_DIR / self.safe_title
        folder.mkdir(parents=True, exist_ok=True)
        return folder
