import requests
import csv
from io import StringIO

from database import db_create_link, db_get_sent
from utils import extract_domain


def parse_sheet_save_url(spread_sheet_id: str, sheet_names: list):
    """Parse a google sheet and save to sqlite3 db"""
    print(f"Opening sheet id {spread_sheet_id}")
    for sheet_name in sheet_names:
        print(f"Sheet: {sheet_name}")
        url = (
            "https://docs.google.com/spreadsheets/d/"
            + spread_sheet_id
            + "/gviz/tq?tqx=out:csv&sheet="
            + sheet_name
        )

        response = requests.get(url)

        data = response.content.decode("utf-8")

        f = StringIO(data)

        reader = csv.reader(f)

        for row in reader:
            link = extract_domain(row[0])

            # Check if email has already been sent to domain
            if not db_get_sent(domain=link):
                db_create_link(link=link)
