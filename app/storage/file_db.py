from __future__ import annotations

from pathlib import Path

from app.config import DB_DIR
from app.models.entities import Chapter, Novel
from app.utils.files import read_json, sanitize_filename, write_json


class FileDB:
    def __init__(self, root: Path | None = None):
        self.root = root or DB_DIR
        self.root.mkdir(parents=True, exist_ok=True)

    def _novel_dir(self, novel_title: str) -> Path:
        path = self.root / sanitize_filename(novel_title)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _metadata_path(self, novel_title: str) -> Path:
        return self._novel_dir(novel_title) / "metadata.json"

    def _chapter_path(self, novel_title: str, chapter: Chapter) -> Path:
        return self._novel_dir(novel_title) / f"{sanitize_filename(chapter.title)}.txt"

    def save_novel(self, novel: Novel) -> None:
        payload = {
            "title": novel.title,
            "author": novel.author,
            "url": novel.url,
            "desc": novel.desc,
            "website": novel.website,
            "image": novel.image,
            "downloaded_set": sorted(novel.downloaded_set),
            "last_error": novel.last_error,
            "chapter_list": [
                {"title": ch.title, "url": ch.url, "order": ch.order}
                for ch in novel.chapter_list
            ],
        }
        write_json(self._metadata_path(novel.title), payload)

    def set_chapter(self, novel: Novel, chapter: Chapter) -> None:
        path = self._chapter_path(novel.title, chapter)
        path.write_text(chapter.content, encoding="utf-8")
        novel.downloaded_set.add(chapter.title)
        self.save_novel(novel)

    def get_chapter_content(self, novel: Novel, chapter: Chapter) -> str | None:
        path = self._chapter_path(novel.title, chapter)
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")

    def load_novel(self, novel_title: str) -> Novel | None:
        metadata_path = self._metadata_path(novel_title)
        if not metadata_path.exists():
            return None

        data = read_json(metadata_path)
        novel = Novel(
            title=data["title"],
            author=data.get("author", "Unknown"),
            url=data.get("url", ""),
            desc=data.get("desc", ""),
            website=data.get("website", ""),
            image=data.get("image", ""),
            chapter_list=[
                Chapter(
                    title=item["title"],
                    url=item["url"],
                    order=item.get("order", index),
                )
                for index, item in enumerate(data.get("chapter_list", []), start=1)
            ],
            downloaded_set=set(data.get("downloaded_set", [])),
        )
        novel.last_error = data.get("last_error", "")

        hydrated_downloaded = set()
        for chapter in novel.chapter_list:
            content = self.get_chapter_content(novel, chapter)
            if content:
                chapter.content = content
                hydrated_downloaded.add(chapter.title)

        novel.downloaded_set = hydrated_downloaded
        return novel

    def list_novel_titles(self) -> list[str]:
        titles: list[str] = []
        for item in self.root.iterdir():
            if item.is_dir() and (item / "metadata.json").exists():
                titles.append(item.name)
        return sorted(titles, key=str.lower)

    def get_all(self) -> list[Novel]:
        novels: list[Novel] = []
        for title in self.list_novel_titles():
            try:
                novel = self.load_novel(title)
                if novel:
                    novels.append(novel)
            except Exception:
                continue
        return novels

    def delete_novel(self, novel_title: str) -> bool:
        folder = self._novel_dir(novel_title)
        if not folder.exists():
            return False
        for path in folder.glob("**/*"):
            if path.is_file():
                path.unlink(missing_ok=True)
        for path in sorted(folder.glob("**/*"), reverse=True):
            if path.is_dir():
                path.rmdir()
        folder.rmdir()
        return True