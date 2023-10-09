from urllib.parse import urlparse, unquote

from selenium import webdriver
from selenium.webdriver.common.by import By


def get_image_name(url):
    parsed_url = urlparse(url)
    return unquote(parsed_url.path.split('/')[-1])


def get_path_and_name(url, image_name=None, extension='.jpg') -> tuple[str, str]:
    if not image_name:
        image_name = get_image_name(url)
    image_name = image_name.replace(' ', '_').lower()
    if extension:
        image_name = image_name.split('.')[0]
        image_name += extension

    return f'internal/img/covers/{image_name}', image_name


def download_with_screenshot(driver: webdriver.Chrome, novel_title: str, img_src: str) -> str:
    image_path, image_name = get_path_and_name(img_src, novel_title, '.png')

    main_window = driver.current_window_handle
    # Open image in a new tab
    driver.execute_script(f'window.open("{img_src}", "_blank");')
    driver.switch_to.window(driver.window_handles[-1])
    driver.find_element(By.CSS_SELECTOR, 'body > img').screenshot(image_path)
    driver.close()
    driver.switch_to.window(main_window)

    return image_name
