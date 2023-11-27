import os
import sys
import json
import threading
import logging
import asyncio

from openai import AsyncOpenAI

from database import db_get_links_for_parsing, db_update_link_record

api_key = os.getenv("OPENAPI_KEY")

if not api_key:
    print("No api key found in environment")
    sys.exit()

client = AsyncOpenAI(api_key=api_key)


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

    In terms of the 'contact_name' key, this can either be company name OR an actual name. Sometimes the name of the person is reflected by the email. for example john@example.com.
    """,
    }
    {extra_instructions}

    return user_message


async def async_complete_chat(content: str, keys: list, extra_instructions: str = None):
    message = get_user_message(content, keys, extra_instructions)

    completion = await client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        response_format={"type": "json_object"},
        messages=[system_message, message],
    )

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


async def async_ai_parser(outfolder: str, keys: list, attempts: int = 3):
    links = db_get_links_for_parsing()

    for id, path in links:
        file_path = f"{outfolder}/{path}.txt"
        print(f"Opening {file_path}")
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        count = 0
        data = {}

        while (
            not has_required_keys(json_obj=data, required_keys=keys)
            and count < attempts
        ):
            print(f"Parsing {path} [attempt {count+1}/{attempts}]")

            extra_instructions = ""
            if count > 0:
                extra_instructions = (
                    f"REMEMBER to return json object with these key: {keys}"
                )

            count += 1

            try:
                # Wait for the async function with a timeout
                response = await asyncio.wait_for(
                    async_complete_chat(content, keys, extra_instructions), timeout=20
                )
                data.update(json.loads(response.choices[0].message.content))
            except (json.JSONDecodeError, asyncio.TimeoutError) as e:
                logging.error(f"Error or timeout for {path}: {e}")
                continue  # Skip to the next iteration on error or timeout

        print(f"Updating {path} in database")

        if data:
            db_update_link_record(
                link_id=id,
                new_email=data.get("e-mail", ""),
                new_contact_name=data.get("contact_name", ""),
                new_industry=data.get("industry", ""),
                new_city=data.get("city", ""),
                new_area=data.get("area", ""),
                new_parsed=1,
            )
        else:
            logging.warning(f"No data for {path}")
            db_update_link_record(link_id=id, new_parsed=1)


""" def ai_parser(outfolder: str, keys: list, attempts: int = 3):
    links = db_get_links_for_parsing()

    for id, path in links:
        file_path = f"{outfolder}/{path}.txt"
        print(f"Opening {file_path}")
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        count = 0
        data = {}
        result = None

        while not has_required_keys(json_obj=data, required_keys=keys) and count < attempts:
            print(f"Parsing {path} [attempt {count+1}/{attempts}]")

            extra_instructions = ""
            if count > 0:
                extra_instructions = f"REMEMBER to return json object with these key: {keys}"

            count += 1

            def call_complete_chat():
                nonlocal result  # Use nonlocal to modify the outer scope variable
                try:
                    response = complete_chat(content, keys, extra_instructions)
                    result = json.loads(response.choices[0].message.content)
                except json.JSONDecodeError as e:
                    logging.error(f"Error loading json for {path}: {e}")
                    result = None

            chat_thread = threading.Thread(target=call_complete_chat)
            chat_thread.start()
            chat_thread.join(timeout=20)

            if chat_thread.is_alive():
                logging.error(f"Timeout occurred for {path}")
                chat_thread.join()
                continue

            if result:
                data.update(result)

        print(f"Updating {path} in database")

        if data:
            db_update_link_record(
                link_id=id,
                new_email=data.get("e-mail", ""),
                new_contact_name=data.get("contact_name", ""),
                new_industry=data.get("industry", ""),
                new_city=data.get("city", ""),
                new_area=data.get("area", ""),
                new_parsed=1,
            )
        else:
            logging.warning(f"No data for {path}")
            db_update_link_record(link_id=id, new_parsed=1) """
