import difflib

from tqdm import tqdm
from datasketch import MinHash, MinHashLSH
from concurrent.futures import ProcessPoolExecutor, as_completed

from logic.entities import Novel
from logic.filters import ContentFilter

def _build_minhash(chapter, num_perm: int) -> tuple:
    """
    Accept a Chapter instance and return (chapter, MinHash).
    """
    tokens = chapter.content.lower().split()
    mh = MinHash(num_perm=num_perm)
    for t in tokens:
        mh.update(t.encode("utf8"))
    return chapter, mh

class ContentFilterLSH(ContentFilter):
    def filter_content(self, novel: Novel, threshold: float = 0.75, num_perm: int = 128) -> Novel:
        # Build MinHash signature for every chapter
        minhashes = []
        n = len(novel.chapter_list)

        with ProcessPoolExecutor() as executor:
            # Each worker runs _build_minhash(chapter, num_perm) → (chapter, MinHash)
            futures = [
                executor.submit(_build_minhash, ch, num_perm) for ch in novel.chapter_list
            ]

            for future in tqdm(as_completed(futures),
                               total=n,
                               desc="Build MinHash"):
                chapter, mh = future.result()
                minhashes.append((chapter, mh))

        # Insert into LSH index
        lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
        for idx, (ch, mh) in enumerate(minhashes):
            lsh.insert(str(idx), mh)

        # Now iterate over chapters in original order and check “candidates” in LSH
        filtered = []
        dup = []
        seen_indices = set()
        for i, (ch, mh) in enumerate(minhashes):
            if i in seen_indices:
                # Already marked as duplicate earlier
                continue

            # Query LSH for any existing near‐duplicates
            candidates = lsh.query(mh)
            # candidates is a list of string‐indices whose MinHash Jaccard is ≥ threshold
            # We still need to confirm with exact SequenceMatcher if you want “true”
            is_dup = False
            for c in candidates:
                c_idx = int(c)
                if c_idx == i or c_idx in seen_indices:
                    continue
                candidate_chapter = minhashes[c_idx][0]
                print(f"Possible duplicate chapter detected: '{ch.title}' is similar to "
                      f"'{candidate_chapter.title}'. Evaluating.")
                # Double‐check with SequenceMatcher.ratio()
                r = difflib.SequenceMatcher(
                    None,
                    ch.content.strip().lower(),
                    candidate_chapter.content.strip().lower()
                ).ratio()
                print(f"Duplicate chapter detected: '{ch.title}' is similar to "
                      f"'{candidate_chapter.title}' (similarity: {r:.2f}). Removing it.")
                if r >= threshold:
                    is_dup = True
                    seen_indices.add(i)
                    break
            if is_dup:
                dup.append(ch.title)
            else:
                filtered.append(ch)

        novel.chapter_list = filtered
        print('Total duplicate chapter detected: ', len(dup))
        print(*dup, sep="\n")

        return novel
