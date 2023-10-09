import copy
import os
import shutil
import pickle

from logic.entities import Novel, Chapter
from utils import string_matching


def sanitize_filename(filename: str) -> str:
    invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


class SimpleFileDB:
    def __init__(self, db_location='internal/database'):
        self.db_location = db_location
        if not os.path.exists(db_location):
            os.makedirs(db_location, exist_ok=True)

    def _get_file_path(self, key):
        return os.path.join(self.db_location, key + '.pkl')

    def _get_novel_folder_path(self, novel_title):
        sanitized_novel_title = sanitize_filename(novel_title)
        novel_folder_path = os.path.join(self.db_location, sanitized_novel_title)
        if not os.path.exists(novel_folder_path):
            os.makedirs(novel_folder_path)

        return novel_folder_path

    def _get_chapter_file_path(self, novel_title, chapter_title):
        sanitized_chapter_title = sanitize_filename(chapter_title)

        novel_folder_path = self._get_novel_folder_path(novel_title)
        return os.path.join(novel_folder_path, f"{sanitized_chapter_title}.pkl")

    def set_chapter(self, novel: Novel, chapter: Chapter):
        chapter_path = self._get_chapter_file_path(novel.title, chapter.title)
        with open(chapter_path, 'wb') as file:
            pickle.dump(chapter.content, file)

    def get_chapter_content(self, novel: Novel, chapter: Chapter):
        chapter_path = self._get_chapter_file_path(novel.title, chapter.title)
        try:
            with open(chapter_path, 'rb') as file:
                return pickle.load(file)
        except FileNotFoundError:
            return None

    def _get_novel_file_path(self, novel_title):
        novel_folder_path = self._get_novel_folder_path(novel_title)
        return os.path.join(novel_folder_path, "metadata.pkl")

    def save_novel(self, novel: Novel):
        novel_copy = copy.deepcopy(novel)

        # Strip the content from each chapter in the copied novel
        for chapter in novel_copy.chapter_list:
            chapter.content = ""

        novel_path = self._get_novel_file_path(novel.title)
        with open(novel_path, 'wb') as file:
            pickle.dump(novel_copy, file)

    def load_novel(self, novel_title: str) -> Novel | None:
        novel_path = self._get_novel_file_path(novel_title)
        with open(novel_path, 'rb') as file:
            novel = pickle.load(file)
        if novel is None:
            return None

        chapters_files = self.get_saved_chapters(novel_title)

        # Populate chapter content from individual chapter files
        for chapter in novel.chapter_list:
            content = self.get_chapter_content(novel, chapter)
            if content:
                chapter.content = content
                novel.downloaded_set.add(chapter.title)

        # Sync chapters
        self.save_novel(novel)

        return novel

    def delete_novel(self, novel_title):
        novel_path = self._get_novel_folder_path(novel_title)
        try:
            shutil.rmtree(novel_path)
            return True
        except FileNotFoundError:
            return False

    def set(self, key, obj):
        with open(self._get_file_path(key), 'wb') as file:
            pickle.dump(obj, file)

    def get(self, key):
        try:
            with open(self._get_file_path(key), 'rb') as file:
                return pickle.load(file)
        except FileNotFoundError:
            return None

    def delete(self, key):
        try:
            os.remove(self._get_file_path(key))
        except FileNotFoundError:
            pass

    def keys(self):
        return [file for file in os.listdir(self.db_location)]

    def get_saved_chapters(self, novel_name: str) -> list[str]:
        files = [file for file in os.listdir(self._get_novel_folder_path(novel_name))]
        chapters = [file for file in files if file.endswith(".pkl") and file != "metadata.pkl"]

        return chapters

    def get_all(self):
        return [self.load_novel(key) for key in self.keys()]
