from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException


driver = webdriver.Chrome()


try:
    driver.get("http://localhost:8080/screenshoter")
    body = driver.find_element(By.TAG_NAME, 'body')
    for element in body.find_elements(By.CLASS_NAME, '_FSU-target'):
        try:
            element.screenshot(f'screenshots/{element.get_attribute('id')}.png')
        except WebDriverException:
            ...


finally:
    driver.quit()
