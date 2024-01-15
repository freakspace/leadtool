import json
import logging
import asyncio

from driver import get_content_from_url

from database import tables, check_table_exists
from sheets import parse_sheet_save_url, add_sent
from ai_parser import AiParser
from services import get_links, create_user

# Configure logging
logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def main(config):
    # Create tables is they don't exists
    for key in tables:
        if not check_table_exists(key):
            print(f"Creating table: {key}")
            tables[key]()

    while True:
        print(
            """
    Type a to get links from google sheet
    Type b to scrape content from links (Will open Chrome)
    Type c to extract info from content using ChatGPT
    Type d to add user
    Type e to add 'sent'
    Type x to exit
    """
        )

        action = input()
        actions = ["a", "b", "c", "d", "x"]
        if action in actions:
            break

        print("We didn't quite catch that.. Try again.")

    if action == "a":
        parse_sheet_save_url(
            spread_sheet_id=config["google_sheets"]["sheet_id"],
            sheet_names=config["google_sheets"]["sheet_names"],
        )

    if action == "b":
        links = get_links()
        get_content_from_url(links=links, outfolder=config["out_files_folder"])

    if action == "c":
        parser = AiParser(
            outfolder=config["out_files_folder"], keys=config["aiparser"]["keys"]
        )
        await parser.run(image_classification=False)

    if action == "d":
        print("Name: ")
        username = input()
        print("Password: ")
        pasword = input()
        print("Superuser [n/y] ")
        superuser = input()
        is_superuser = superuser == "y"
        print(f"Creating user {username}. Superuser: {is_superuser}")
        create_user(username=username, password=pasword, superuser=is_superuser)

    if action == "e":
        add_sent(spread_sheet_id=config["google_sheets"]["sheet_id"], sheet_name="sent")

    if action == "x":
        pass


if __name__ == "__main__":
    with open("config.json") as config_file:
        config = json.load(config_file)

    asyncio.run(main(config=config))
