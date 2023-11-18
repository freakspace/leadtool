import os
import sys
import json

import logging

from openai import OpenAI

from database import db_get_links_for_parsing, db_update_link_record

api_key = os.getenv("OPENAPI_KEY")

if not api_key:
    print("No api key found in environment")
    sys.exit()

client = OpenAI(api_key=api_key)


system_message = {
    "role": "system",
    "content": "You are a helpful assistant designed to output JSON. You will be given a piece of content (from a website), and instructed by the user to extract information. Remember to return as JSON. Do not return any translations, only the data.",
}


def get_user_message(content: str, keys: list, extra_instructions: str = None):
    user_message = {
        "role": "user",
        "content": f"""
    Please extract the following information from the content. Remember to not translate the data, only return the data.:

    {', '.join(str(key) for key in keys)}

    If you are not sure, write None

    CONTENT:
    {content}

    Remember to output as JSON and write the json key EXACTLY as written above {', '.join(str(key) for key in keys)}
    """,
    }
    {extra_instructions}

    return user_message


def complete_chat(content: str, keys: list, extra_instructions: str = None):
    message = get_user_message(content, keys, extra_instructions)
    print("TEST A")
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"},
        messages=[system_message, message],
    )
    print("TEST B")
    return completion


def has_required_keys(json_obj, required_keys):
    """
    Check if the JSON object has all the required keys.

    Args:
    json_obj (dict): The JSON object (dictionary) to check.
    required_keys (list): A list of keys that must be present in the JSON object.

    Returns:
    bool: True if all required keys are present, False otherwise.
    """
    return all(key in json_obj for key in required_keys)


def ai_parser(outfolder: str, keys: list, attempts: int = 3):
    links = db_get_links_for_parsing()

    for id, path in links:
        file_path = f"{outfolder}/{path}.txt"
        print(f"Opening {file_path}")
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        count = 0
        data = {}

        while not has_required_keys(json_obj=data, required_keys=keys):
            print(f"Parsing {path} [attempt {count+1}/{attempts}]")
            if count == attempts:
                db_update_link_record(link_id=id, new_parsed=1)
                logging.warning(f"No data for {path}")
                break

            extra_instructions = ""

            if count > 0:
                extra_instructions = (
                    f"REMEMBER to return json object with these key: {keys}"
                )

            try:
                response = complete_chat(content, keys, extra_instructions)

                data = json.loads(response.choices[0].message.content)

            except json.JSONDecodeError as e:
                logging.error(f"Error loading json for {path}: {e}")

            count += 1

        print(f"Updating {path} in database")

        db_update_link_record(
            link_id=id,
            new_email=data["e-mail"],
            new_contact_name=data["contact_name"],
            new_industry=data["industry"],
            new_city=data["city"],
            new_area=data["area"],
            new_parsed=1,
        )

        print(data)
        # {'e-mail': 'None', 'contact_name': 'None', 'industry': 'None', 'city': 'None', 'area': 'None'}
