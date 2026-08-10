from __future__ import annotations

import json

from app.models.entities import Novel


class NovelExporter:
    def export_txt_split(self, novel: Novel, max_per_file: int = 300) -> list[str]:
        output_paths: list[str] = []
        chapters = [ch for ch in sorted(novel.chapter_list, key=lambda c: c.order) if ch.content.strip()]
        if not chapters:
            raise ValueError("There are no downloaded chapters to export.")

        volume = 1
        count = 0
        current_file = None

        try:
            for chapter in chapters:
                if current_file is None or count >= max_per_file:
                    if current_file:
                        current_file.close()
                    path = novel.export_folder() / f"{novel.safe_title}_{volume}.txt"
                    current_file = path.open("w", encoding="utf-8")
                    output_paths.append(str(path))
                    volume += 1
                    count = 0

                current_file.write(f"{'=' * 10}\n{chapter.title}\n{'=' * 10}\n")
                current_file.write(chapter.content.strip() + "\n\n")
                count += 1
        finally:
            if current_file:
                current_file.close()

        return output_paths

    def export_single_txt(self, novel: Novel) -> str:
        chapters = [ch for ch in sorted(novel.chapter_list, key=lambda c: c.order) if ch.content.strip()]
        if not chapters:
            raise ValueError("There are no downloaded chapters to export.")

        path = novel.export_folder() / f"{novel.safe_title}_full.txt"
        with path.open("w", encoding="utf-8") as handle:
            handle.write(f"{novel.title}\n")
            handle.write(f"Author: {novel.author}\n")
            handle.write(f"Source: {novel.website}\n")
            handle.write(f"URL: {novel.url}\n\n")
            for chapter in chapters:
                handle.write(f"{'=' * 10}\n{chapter.title}\n{'=' * 10}\n")
                handle.write(chapter.content.strip() + "\n\n")
        return str(path)

    def export_metadata(self, novel: Novel) -> str:
        path = novel.export_folder() / f"{novel.safe_title}_metadata.json"
        payload = {
            "title": novel.title,
            "author": novel.author,
            "website": novel.website,
            "url": novel.url,
            "description": novel.desc,
            "downloaded": novel.downloaded_count,
            "total_chapters": novel.total_chapters,
            "chapters": [
                {"title": ch.title, "url": ch.url, "order": ch.order, "downloaded": ch.is_downloaded}
                for ch in sorted(novel.chapter_list, key=lambda c: c.order)
            ],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path)
