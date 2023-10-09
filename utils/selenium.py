from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def get_element(element_or_driver, by=By.ID, key: str = None) -> WebElement | None:
    elements = element_or_driver.find_elements(by, key)
    if not elements:
        return None
    return elements[0]


def wait_and_click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView();", element)
    wait = WebDriverWait(driver, 10)
    wait.until(EC.element_to_be_clickable(element))

    driver.execute_script("arguments[0].click();", element)
