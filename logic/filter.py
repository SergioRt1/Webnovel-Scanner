from collections import Counter
from .entities import Novel

class ContentFilter:
    def filter_content(self, novel: Novel) -> Novel:
        num_chapters = len(novel.chapter_list)
        filtered_chapters = []

        window_lines = []
        start_index = -1
        start_len = 0
        current_len = 0
        end_index = 1

        for i in range(num_chapters):
            if start_index >= 0:
                window_lines = window_lines[start_len:]
            else:
                first_chapter_lines = novel.chapter_list[0].content.splitlines()
                start_len = len(first_chapter_lines)
                window_lines.extend([line.strip().lower() for line in first_chapter_lines])
                
            if end_index < num_chapters:
                end_chapter_lines = novel.chapter_list[end_index].content.splitlines()
                current_len = len(end_chapter_lines)
                window_lines.extend([line.strip().lower() for line in end_chapter_lines])

            line_count = Counter(window_lines)

            filtered_lines = []
            chapter_lines = novel.chapter_list[i].content.splitlines()

            for line in chapter_lines:
                stripped_line = line.strip().lower()
                if line_count[stripped_line] > 1 and len(stripped_line)> 10:
                    print(f"Duplicated block detected in chapter {i+1}: '{line}'")
                else:
                    filtered_lines.append(line)

            novel.chapter_list[i].content = '\n'.join(filtered_lines)

            start_len = current_len

        return novel
