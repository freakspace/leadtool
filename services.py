import os

import requests
from dotenv import load_dotenv

load_dotenv()

api_endpoint = os.getenv("API_ENDPOINT")

print(f"Connecting to: {api_endpoint}")

if not api_endpoint:
    raise Exception("You need to add API_ENDPOINT to the environment")


def update_link_record(
    link_id: int,
    content_file: str = None,
    email: str = None,
    contact_name: str = None,
    pronoun: str = None,
    industry: str = None,
    city: str = None,
    area: str = None,
    parsed: int = 0,
    invalid: int = 0,
    classification: int = None,
):
    url = f"http://{api_endpoint}/api/update_link/{link_id}"

    data = {
        "content_file": content_file,
        "email": email,
        "contact_name": contact_name,
        "pronoun": pronoun,
        "industry": industry,
        "city": city,
        "area": area,
        "parsed": parsed,
        "invalid": invalid,
        "classification": classification,
    }

    response = requests.post(url, json=data)

    if response.status_code == 200:
        return
    else:
        raise Exception("Bad request")


def check_sent(domain: str = None, email: str = None):
    url = f"http://{api_endpoint}/api/check_sent"

    data = {"domain": domain, "email": email}

    response = requests.post(url, json=data)
    if response.status_code == 200:
        data = response.json()
        return data["sent"]
    else:
        raise Exception("Bad request")


def create_link(link: str):
    url = f"http://{api_endpoint}/api/create_link"

    data = {"link": link}

    response = requests.post(url, json=data)
    if response.status_code == 200:
        return
    else:
        raise Exception("Bad request")


def get_links():
    url = f"http://{api_endpoint}/api/links"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["links"]
    else:
        raise Exception("Bad request")


def get_links_for_parsing():
    # Get all links ready for AI parser
    url = f"http://{api_endpoint}/api/links_for_parsing"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["links"]
    else:
        raise Exception("Bad request")


def get_campaigns():
    # Get all links ready for AI parser
    url = f"http://{api_endpoint}/api/campaigns"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data["campaigns"]
    else:
        raise Exception("Bad request")


def create_user(username: str, password: str, superuser: bool):
    # Get all links ready for AI parser
    url = f"http://{api_endpoint}/api/create_user"

    data = {
        "username": username,
        "password": password,
        "superuser": superuser,
    }

    response = requests.post(url, json=data)

    if response.status_code == 200:
        return
    else:
        raise Exception("Bad request")
