import logging
import os

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from PIL import Image

from services import update_link_record

# TODO Maybe crawl a couple of pages and get the info?


def merge_images(image_path_1, image_path_2, merged_image_path):
    # Open the first and second image
    image1 = Image.open(image_path_1)
    image2 = Image.open(image_path_2)

    # Calculate dimensions for the merged image
    width = max(image1.width, image2.width)
    height = image1.height + image2.height

    # Create a new image with the appropriate height and width
    merged_image = Image.new("RGB", (width, height))

    # Paste the first image at the top
    merged_image.paste(image1, (0, 0))

    # Paste the second image below the first
    merged_image.paste(image2, (0, image1.height))

    # Resize the image to 50% of its current size
    new_width = int(merged_image.width * 0.5)
    new_height = int(merged_image.height * 0.5)
    merged_image = merged_image.resize((new_width, new_height))

    # Save the merged image
    merged_image.save(merged_image_path, "JPEG", quality=60)


def get_content_from_url(links: list, outfolder: str):
    # Set the desired capabilities with the page load strategy
    options = FirefoxOptions()
    options.set_capability("pageLoadStrategy", "normal")

    # Instantiate the Chrome driver with the specified capabilities
    driver = webdriver.Firefox(options=options)

    # Set the page load timeout
    driver.set_page_load_timeout(20)  # Adjust the timeout as needed

    # Make the browser full screen
    driver.maximize_window()

    for record in links:
        id, link = record

        try:
            driver.get("http://" + link)
        except TimeoutException:
            logging.error(f"Timeout error for link {link}")
            # continue
        except WebDriverException as e:
            if "ERR_NAME_NOT_RESOLVED" in str(e):
                update_link_record(link_id=id, invalid=True)
                logging.error(f"ERR_NAME_NOT_RESOLVED: {link}")
            if "DNS_PROBE_FINISHED_NXDOMAIN" in str(e):
                update_link_record(link_id=id, invalid=True)
                logging.error(f"DNS_PROBE_FINISHED_NXDOMAIN: {link}")
            if "dnsNotFound" in str(e):
                update_link_record(link_id=id, invalid=True)
                logging.error(f"dnsNotFound: {link}")
            else:
                logging.error(f"Error: {e}")
            continue
        except Exception as e:
            logging.error(f"Error fetching link {link}: {e}")
            continue

        try:
            text_content = driver.find_element(by=By.TAG_NAME, value="body").text
            text_file_path = f"{outfolder}/{link}.txt"
            screenshot_final = f"{outfolder}/{link}.png"  # Path for the screenshot
            screenshot_1 = f"{outfolder}/{link}_1.png"
            screenshot_2 = f"{outfolder}/{link}_2.png"

            with open(text_file_path, "w", encoding="utf-8") as out_file:
                out_file.write(text_content)

            driver.save_screenshot(screenshot_1)

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            driver.save_screenshot(screenshot_2)

            # Merge screenshots
            merge_images(screenshot_1, screenshot_2, screenshot_final)

            if os.path.exists(screenshot_final):
                print(f"Updating link: {link}")
                update_link_record(link_id=id, content_file=link)
                os.remove(screenshot_1)
                os.remove(screenshot_2)
            else:
                logging.error(f"Screenshot doesnt exist for {link}")
        # TODO Update link record with error message so it can be skipped next time
        except Exception as e:
            logging.error(f"Error processing link {link}: {e}")
            update_link_record(link_id=id, invalid=True)

    driver.quit()
