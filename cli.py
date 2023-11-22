import json
import logging

from driver import get_content_from_url

from database import tables, check_table_exists, db_get_links
from sheets import parse_sheet_save_url
from ai_parser import ai_parser

# Configure logging
logging.basicConfig(
    filename="app.log",
    filemode="a",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def main(config):
    # Create tables is they don't exists
    for key in tables:
        if not check_table_exists(key):
            print(f"Creating table: {key}")
            tables[key]()

    while True:
        print(
            """
    Type a to parse google sheet
    Type b to parse links (Will open Chrome)
    Type c to extract info from content
    Type x to exit
    """
        )

        action = input()

        if action == "a" or action == "b" or action == "c" or action == "x":
            break

        print("We didn't quite catch that.. Try again.")

    if action == "a":
        parse_sheet_save_url(
            spread_sheet_id=config["google_sheets"]["sheet_id"],
            sheet_names=config["google_sheets"]["sheet_names"],
        )

    if action == "b":
        links = db_get_links()
        get_content_from_url(links=links, outfolder=config["out_files_folder"])

    if action == "c":
        ai_parser(outfolder=config["out_files_folder"], keys=config["aiparser"]["keys"])

    if action == "x":
        pass


if __name__ == "__main__":
    with open("config.json") as config_file:
        config = json.load(config_file)

    main(config=config)
