from __future__ import annotations

import difflib
from concurrent.futures import ProcessPoolExecutor, as_completed

from datasketch import MinHash, MinHashLSH

from app.models.entities import Novel, Chapter


def _build_minhash(chapter: Chapter, num_perm: int) -> tuple[Chapter, MinHash]:
    tokens = chapter.content.lower().split()
    mh = MinHash(num_perm=num_perm)
    for token in tokens:
        mh.update(token.encode("utf-8"))
    return chapter, mh


class ContentFilterLSH:
    def filter_content(self, novel: Novel, threshold: float = 0.75, num_perm: int = 128) -> Novel:
        if not novel.chapter_list:
            return novel

        minhashes: list[tuple[Chapter, MinHash] | None] = [None] * len(novel.chapter_list)

        with ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(_build_minhash, chapter, num_perm): idx
                for idx, chapter in enumerate(novel.chapter_list)
                if chapter.content.strip()
            }

            for future in as_completed(futures):
                idx = futures[future]
                chapter, mh = future.result()
                minhashes[idx] = (chapter, mh)

        valid_items = [(idx, item[0], item[1]) for idx, item in enumerate(minhashes) if item is not None]
        if not valid_items:
            return novel

        lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        for idx, _chapter, mh in valid_items:
            lsh.insert(str(idx), mh)

        filtered: list[Chapter] = []
        seen_indices: set[int] = set()

        for idx, chapter in enumerate(novel.chapter_list):
            if minhashes[idx] is None:
                filtered.append(chapter)
                continue

            if idx in seen_indices:
                continue

            _, mh = minhashes[idx]
            for candidate in lsh.query(mh):
                candidate_idx = int(candidate)
                if candidate_idx <= idx or candidate_idx in seen_indices:
                    continue

                candidate_chapter = minhashes[candidate_idx][0]
                ratio = difflib.SequenceMatcher(
                    None,
                    chapter.content.strip().lower(),
                    candidate_chapter.content.strip().lower(),
                ).ratio()

                if ratio >= threshold:
                    seen_indices.add(candidate_idx)

            filtered.append(chapter)

        novel.chapter_list = filtered
        novel.downloaded_set = {ch.title for ch in filtered if ch.is_downloaded}
        return novel
