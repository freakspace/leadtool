import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from services import update_link_record

# TODO Maybe crawl a couple of pages and get the info?


def get_content_from_url(links: list, outfolder: str):
    # Set the desired capabilities with the page load strategy
    options = FirefoxOptions()
    options.set_capability("pageLoadStrategy", "eager")

    # Instantiate the Chrome driver with the specified capabilities
    driver = webdriver.Firefox(options=options)

    # Set the page load timeout
    driver.set_page_load_timeout(30)  # Adjust the timeout as needed

    for record in links:
        id, link = record

        try:
            driver.get("http://" + link)
        except TimeoutException:
            logging.error(f"Timeout error for link {link}")
            continue
        except WebDriverException as e:
            if "ERR_NAME_NOT_RESOLVED" in str(e):
                update_link_record(link_id=id, invalid=True)
                logging.error(f"ERR_NAME_NOT_RESOLVED")
            if "DNS_PROBE_FINISHED_NXDOMAIN" in str(e):
                update_link_record(link_id=id, invalid=True)
                logging.error(f"DNS_PROBE_FINISHED_NXDOMAIN")
            else:
                logging.error(f"Error: {e}")
            continue
        except Exception as e:
            logging.error(f"Error fetching link {link}: {e}")
            continue

        try:
            text_content = driver.find_element(by=By.TAG_NAME, value="body").text
            text_file_path = f"{outfolder}/{link}.txt"
            screenshot_file_path = f"{outfolder}/{link}.png"  # Path for the screenshot

            with open(text_file_path, "w", encoding="utf-8") as out_file:
                out_file.write(text_content)

            driver.save_screenshot(screenshot_file_path)  # Save the screenshot
            print(f"Updating link: {link}")
            update_link_record(link_id=id, content_file=link)
        # TODO Update link record with error message so it can be skipped next time
        except Exception as e:
            logging.error(f"Error processing link {link}: {e}")

    driver.quit()
