from __future__ import annotations

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def wait_for(driver: WebDriver, by: By, selector: str, timeout: int = 12) -> WebElement:
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )


def safe_get_text(driver: WebDriver, selector: str, timeout: int = 12) -> str:
    element = wait_for(driver, By.CSS_SELECTOR, selector, timeout)
    return element.text.strip()


def safe_get_attribute(driver: WebDriver, selector: str, attribute: str, timeout: int = 12) -> str | None:
    element = wait_for(driver, By.CSS_SELECTOR, selector, timeout)
    return element.get_attribute(attribute)


def safe_find_all(driver: WebDriver, selector: str, timeout: int = 12) -> list[WebElement]:
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, selector)) > 0
    )
    return driver.find_elements(By.CSS_SELECTOR, selector)


def wait_and_click(driver: WebDriver, element: WebElement, timeout: int = 8) -> None:
    WebDriverWait(driver, timeout).until(lambda _driver: element.is_displayed() and element.is_enabled())
    element.click()


def stop_loading(driver: WebDriver) -> None:
    try:
        driver.execute_script("window.stop();")
    except TimeoutException:
        pass
    except Exception:
        pass
