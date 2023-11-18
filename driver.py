import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

from database import db_update_link_record


# TODO Maybe crawl a couple of pages and get the info?
def get_content_from_url(links: list, outfolder: str):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

    for record in links:
        id, link = record

        try:
            driver.get("http://" + link)
        except Exception as e:
            logging.error(f"Error fetching link {link}: {e}")

        text_content = driver.find_element(by=By.TAG_NAME, value="body").text

        file_path = f"{outfolder}/{link}.txt"

        try:
            with open(file_path, "w", encoding="utf-8") as out_file:
                out_file.write(text_content)
        except Exception as e:
            logging.error(f"Error saving content for {link}: {e}")

        db_update_link_record(link_id=id, new_content_file=link)

    driver.quit()
