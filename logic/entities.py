import os

from utils import constants
from db import img, file as filemanager


class Chapter:
    def __init__(self, title, url):
        self.title = title
        self.url = url
        self.content = ""

    def __str__(self):
        return self.title


class Novel:
    def __init__(self, title: str, author: str, url: str, desc: str,
                 website,
                 image: str = constants.placeholder_image,
                 chapter_list: [Chapter] = None,
                 downloaded_list=None):
        self.title = title
        self.author = author
        self.url = url
        self.desc = desc
        self.image = image
        self.website = website
        # Initialize as an empty list if not provided
        self.chapter_list = chapter_list if chapter_list else []
        self.downloaded_set = downloaded_list if downloaded_list else set()

    def __str__(self):
        return f"'{self.title}' by {self.author}."

    def get_chapters_to_download(self):
        """
        Returns the chapters that are not downloaded yet.
        """
        return [ch for ch in self.chapter_list if ch.title not in self.downloaded_set]

    def get_image_path(self):
        return img.get_image_path(self.image)

    def is_downloaded(self):
        return len(self.get_chapters_to_download()) == 0

    def is_new(self):
        return len(self.get_chapters_to_download()) == len(self.chapter_list)

    def write_to_txt(self, max_per_chapter=300):
        novel_title = filemanager.sanitize_filename(self.title)
        output_folder = os.path.join('Novels', novel_title)
        os.makedirs(output_folder, exist_ok=True)

        volume_count = 1
        chapter_count = 0

        file_path = os.path.join(output_folder, f'{novel_title} {volume_count}.txt')
        file = open(file_path, "w+", encoding="utf-8")

        for chapter in self.chapter_list:
            chapter_count += 1
            if chapter_count >= max_per_chapter:
                volume_count += 1
                chapter_count = 0
                file.close()
                file_path = os.path.join(output_folder, f'{novel_title} {volume_count}.txt')
                file = open(file_path, "w+", encoding="utf-8")
            file.write(f'\n--------\n{chapter.title}\n')
            file.write('\n' + chapter.content + '\n')

        file.close()
