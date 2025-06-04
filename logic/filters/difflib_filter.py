import difflib

from logic.entities import Novel
from logic.filters import ContentFilter

# -------------------------------
# Content filter that removes near-duplicate chapters
# -------------------------------

class DiffContentFilter(ContentFilter):
    def filter_content(self, novel: Novel, threshold: float = 0.75, window_size: int = 1) -> Novel:
        """
        Removes duplicate chapters from the novel by comparing chapter content only against
        the last 'window_size' accepted chapters. If the similarity ratio between the new chapter
        and any chapter in the window is above the threshold, the new chapter is considered a duplicate.
        """
        filtered_chapters = []
        print("")
        i = 0
        count = 0
        for chapter in novel.chapter_list:
            i+=1

            normalized_content = chapter.content.strip().lower()
            duplicate_found = False

            # Only compare against the last 'window_size' accepted chapters
            window = filtered_chapters[-window_size:] if len(filtered_chapters) >= window_size else filtered_chapters
            print(f"{i}/{len(novel.chapter_list)}")
            for accepted in window:
                accepted_content = accepted.content.strip().lower()

                matcher = difflib.SequenceMatcher(None, normalized_content, accepted_content)
                ratio = matcher.ratio()
                if ratio >= threshold:
                    print("\033[A\r\033[K", end='')
                    print("\033[A\r\033[K", end='')
                    print("\033[A\r\033[K", end='')
                    print(f"Duplicate chapter detected: '{chapter.title}' is similar to "
                          f"'{accepted.title}' (similarity: {ratio:.2f}). Removing it.")
                    duplicate_found = True
                    count+=1
                    break

            if not duplicate_found:
                print("\033[A\r\033[K", end='')  # Delete a line in the CLI, Move up one line, clear the line
                print("\033[A\r\033[K", end='')
                print("\033[A\r\033[K", end='')
                filtered_chapters.append(chapter)

        print('Total duplicate chapter detected: ', count)
        novel.chapter_list = filtered_chapters
        return novel