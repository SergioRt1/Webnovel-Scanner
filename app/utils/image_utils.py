from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By

import requests

from app.config import IMAGE_DIR
from app.utils.files import sanitize_filename


def get_image_filename(url: str, novel_title: str) -> str:
    suffix = Path(urlparse(url).path).suffix or ".jpg"
    return f"{sanitize_filename(novel_title)}{suffix}"


def download_image(url: str, novel_title: str, timeout: int = 15) -> str | None:
    filename = get_image_filename(url, novel_title)
    target = IMAGE_DIR / filename

    try:
        with requests.Session() as session:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            target.write_bytes(response.content)
        return filename
    except requests.RequestException:
        return None

def download_with_screenshot(driver: webdriver.Chrome, novel_title: str, url: str) -> str:
    filename = get_image_filename(url, novel_title)
    image_path = IMAGE_DIR / filename

    main_window = driver.current_window_handle
    # Open image in a new tab
    driver.execute_script(f'window.open("{url}", "_blank");')
    driver.switch_to.window(driver.window_handles[-1])
    ok = driver.find_element(By.CSS_SELECTOR, 'body > img').screenshot(image_path)
    if not ok:
        print('Error downloading', url, image_path)
    driver.close()
    driver.switch_to.window(main_window)

    return filename
