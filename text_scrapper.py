import os
import random
import re
import time
import traceback
from datetime import datetime

import undetected_chromedriver as uc

from logic.selenium_web import webdriver
from logic.selenium_web import Service as ChromeService
from logic.selenium_web import By

from webdriver_manager.chrome import ChromeDriverManager

source_link = 'https://novelusb.com/novel-book/reverend-insanity-novel/chapter-300'
novel_name = "Reverend Insanity"
site_name = "novel usb"
use_undetected_driver = True
max_per_chapter = 300

total_count = 1
volume_count = 1
chapter_count = 0

words_regex = re.compile(r"\W*")


def generate_pattern(input_string):
    string = words_regex.sub("", input_string.lower())
    pattern = r"\W*".join(string)
    return pattern


title_regex = re.compile(r"[#|\-:/\\]+")
novel_name_regex = re.compile(generate_pattern(novel_name), re.IGNORECASE)
site_name_regex = re.compile(generate_pattern(site_name), re.IGNORECASE)
read_regex = re.compile(r"^Read\b", re.IGNORECASE)
online_for_free = re.compile(generate_pattern("Best online light novel reading website"), re.IGNORECASE)
online_free = re.compile(generate_pattern("Online free"), re.IGNORECASE)
all_page = re.compile(generate_pattern("All page"), re.IGNORECASE)
light_novel = re.compile(generate_pattern("Light novel"), re.IGNORECASE)

nonAlpha = re.compile(r'[^a-zA-Z]')

regexes = [read_regex, novel_name_regex, site_name_regex, online_for_free, online_free, all_page, light_novel]


def scroll_to_end(driver):
    delay = 0.5
    delta = 0.1
    if use_undetected_driver:
        delay = random.uniform(1.5, 3)
        delta = random.uniform(0.1, 0.4)

    time.sleep(delay)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(delay + delta)


def levenshtein_distance(s1, s2):
    """
    Calculates the Levenshtein distance between two strings s1 and s2.
    Returns an integer representing the number of edits required to transform s1 into s2.
    """
    matrix = [[i + j for j in range(len(s2) + 1)] for i in range(len(s1) + 1)]

    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            # Calculate the cost of transforming s1[:i] into s2[:j]
            cost = 0 if s1[i - 1] == s2[j - 1] else 1

            # Update the matrix at position (i,j) with the minimum cost of three possible operations
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,  # deletion
                matrix[i][j - 1] + 1,  # insertion
                matrix[i - 1][j - 1] + cost  # substitution or no change
            )
    return matrix[-1][-1]


def similarity_score(str1, str2):
    """
    Calculates the similarity score between two strings using the Levenshtein distance algorithm.
    Returns a float between 0.0 and 1.0, where 1.0 means the strings are identical.
    """
    distance = levenshtein_distance(str1.lower(), str2.lower())
    max_len = max(len(str1), len(str2))
    if max_len == 0:
        return 1.0  # Both strings are empty
    else:
        return 1.0 - (distance / max_len)


def is_substring(substring: str, string: str):
    return substring.lower() in string.lower()


def get_page(url: str, driver, message):
    ok = False
    while not ok:
        try:
            print(f"Loading [{message}] {url}...", end="")
            driver.get(url)
            print(" Loaded")
            scroll_to_end(driver)
        except Exception as ex:
            print("Error loading Page", ex)
            time.sleep(1)
        else:
            ok = True
    time.sleep(0.5)


content_finders = [
    lambda driver: driver.find_elements(By.ID, 'chr-content'),
    lambda driver: driver.find_elements(By.CLASS_NAME, 'chapter-content'),
    lambda driver: driver.find_elements(By.ID, 'chapter-content'),
    lambda driver: driver.find_elements(By.CLASS_NAME, 'chapter-reading-section'),
]


def get_content(driver):
    index = 0
    content = None
    while not content and index < len(content_finders):
        content = content_finders[index](driver)
        index += 1

    return content[-1] if content else None


def get_page_data(content):
    return '\n'.join(filter(lambda t: t.strip(),
                            map(lambda p: p.text,
                                content.find_elements(By.TAG_NAME, 'p')
                                )
                            )
                     )


def find_a_tag(next_buttons_list):
    a_tags = next_buttons_list[-1].find_elements(By.TAG_NAME, "a")
    if a_tags:
        return a_tags[-1].get_attribute('href')


next_chapter_finders = [
    lambda driver: driver.find_elements(By.ID, "next_chap"),
    lambda driver: driver.find_elements(By.CLASS_NAME, "nextchap"),
    lambda driver: driver.find_elements(By.CLASS_NAME, "chapter-reading-pageitem"),
]

next_chapter_getters = [
    lambda next_buttons_list: next_buttons_list[-1].get_attribute('href') if next_buttons_list else None,
    lambda next_buttons_list: find_a_tag(next_buttons_list),
]


def find_next(driver):
    next_button = None
    next_buttons_list = None
    index = 0
    while not next_buttons_list and index < len(next_chapter_finders):
        next_buttons_list = next_chapter_finders[index](driver)
        index += 1

    index = 0
    if next_buttons_list:
        while not next_button and index < len(next_chapter_getters):
            next_button = next_chapter_getters[index](next_buttons_list)
            index += 1

    return next_button


def get_title(driver):
    chapter_title = []
    if len(chapter_title) > 0 and chapter_title[-1].text != '':
        return chapter_title[-1].text
    else:
        return get_title_from_html(driver)


def get_title_from_html(driver):
    title = driver.title
    parts = title_regex.split(title)

    chapter_name = []
    for part in parts:
        part = part.strip()
        if part:
            for regex in regexes:
                part = regex.sub('', part).strip()
            if part:
                chapter_name.append(part)

    if chapter_name:
        return f'{novel_name} - {" ".join(chapter_name)}'
    else:
        return title.strip()


def filter_data(data):
    page_name = site_name.lower()
    lines = data.split('\n')
    result = []
    for line in lines:
        if page_name not in line.lower():
            result.append(line)
    return '\n'.join(result)


def normalize_text(text):
    return nonAlpha.sub('', text).lower()


def check_for_duplicate_paragraphs(novel_text):
    # Split the novel text into paragraphs
    paragraphs = novel_text.split("\n")

    seen_paragraphs = set()  # A set to keep track of paragraphs we've already seen

    duplicates_found = False

    for index, paragraph in enumerate(paragraphs):
        # Remove leading/trailing whitespace and convert to a standard form for comparison
        normalized_paragraph = normalize_text(paragraph).strip()

        # If the paragraph is empty, skip it
        if not normalized_paragraph:
            continue

        # Check if we've seen this paragraph before
        if normalized_paragraph in seen_paragraphs:
            print(f"Duplicate paragraph found at index {index}:")
            print(paragraph)
            print("---")
            duplicates_found = True
        else:
            seen_paragraphs.add(normalized_paragraph)

    if not duplicates_found:
        print("No duplicate paragraphs found.")


def timer_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        print(f"{func.__name__} se ejecutó en {end_time - start_time}")
        return result

    return wrapper


def validate_page(driver, content):
    return not content


@timer_decorator
def download(driver):
    global volume_count, chapter_count, total_count

    file = open(f'{novel_name} {volume_count}.txt', "w+", encoding="utf-8")
    try:
        next_link = source_link
        while next_link and next_link is not None and not next_link.startswith('javascript'):
            get_page(next_link, driver, total_count)
            content = get_content(driver)
            if validate_page(driver, content):
                continue
            data = get_page_data(content)
            data = filter_data(data)
            check_for_duplicate_paragraphs(data)
            chapter_count += 1
            if chapter_count >= max_per_chapter:
                volume_count += 1
                chapter_count = 0
                file.close()
                file = open(f'{novel_name} {volume_count}.txt', "w+", encoding="utf-8")
            file.write(f'\n--------\n{get_title(driver)}\n')
            file.write('\n' + data + '\n')
            next_link = find_next(driver)
            if next_link is None:
                time.sleep(1)
                next_link = find_next(driver)
            if next_link is None or next_link.startswith('javascript'):
                print("Ok out loop")
            total_count += 1
    except Exception as e:
        print("Something went wrong", e)
        traceback.print_exc()
        raise e
    else:
        print("Nothing went wrong")
    finally:
        file.close()


def get_driver_undetected():
    options = webdriver.ChromeOptions()
    options.add_argument("start-maximized")
    driver_service = ChromeService(ChromeDriverManager().install())
    driver = uc.Chrome(options=options, use_subprocess=False, driver_executable_path=driver_service.path)
    driver.maximize_window()

    return driver


def get_driver_default():
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    return driver


def get_driver(use_undetected: bool):
    if use_undetected:
        return get_driver_undetected()
    else:
        return get_driver_default()


def create_folder(target_path='./Novels'):
    create_folder_if_not_exists(target_path)
    target_folder = os.path.join(target_path, novel_name)
    create_folder_if_not_exists(target_folder)
    os.chdir(target_folder)


def create_folder_if_not_exists(target_folder):
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)


def main():
    driver = get_driver(use_undetected_driver)
    create_folder()
    download(driver)
    driver.close()


if __name__ == "__main__":
    main()
