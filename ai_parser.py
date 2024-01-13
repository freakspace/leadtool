import os
import base64
import sys
import json
import logging
import asyncio

from openai import AsyncOpenAI

from services import update_link_record, get_links_for_parsing

# Classify 0-10
# If more than X, parse content

api_key = os.getenv("OPENAPI_KEY", "")

if not api_key:
    print("No api key found in environment")
    sys.exit()

client = AsyncOpenAI(api_key=api_key)


system_message = {
    "role": "system",
    "content": "You are a helpful assistant designed to output JSON. You will be given a piece of content (text from a website), and instructed by the user to extract certain information. Remember to return as JSON. Do not return any translations, only the raw data.",
}


def get_user_message(content: str, keys: list, extra_instructions: str = None):
    user_message = {
        "role": "user",
        "content": f"""
    Please extract the following information from the content. Remember to not translate the data, only return the raw data:

    {', '.join(str(key) for key in keys)}

    If you are not sure, write 'None'

    CONTENT:
    {content}

    EXTRA INSTRUCTIONS:

    Remember to output as JSON and write the json key EXACTLY as it was written before: {', '.join(str(key) for key in keys)}

    In terms of the 'contact_name' key, this can either be company name OR an actual person name. Sometimes the name of the person is reflected by the email. for example john@example.com = 'John'.
    If you return an actual human name, only return the first name AND return pronoun as 'du'. If its a business name return pronoun as 'i', and if the business name has 'aps' in it, omit that part.

    Examples:

    'Lars Larsen': Name = 'Lars' and pronoun = 'du'
    'DK Roof': Name = 'DK Roof' and pronoun = 'i'

    In terms of the 'city' and 'area' only return a single datapoint, not a list. If there are several cities and areas, just return the first one.

    If you are unsure of any of the datapoints, simply just write 'None'
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


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class AiParser:
    def __init__(self, outfolder, keys):
        self.outfolder = outfolder
        self.keys = keys
        self.links = get_links_for_parsing()
        self.attempts = 1

    async def content_parser(self, id, link):
        """Extract content from a given text document"""

        file_path = f"{self.outfolder}/{link}.txt"
        print(f"Opening {file_path}")
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        count = 0
        data = {}

        while (
            not has_required_keys(json_obj=data, required_keys=self.keys)
            and count < self.attempts
        ):
            print(f"Parsing {link} [attempt {count+1}/{self.attempts}]")

            extra_instructions = ""
            if count > 0:
                extra_instructions = (
                    f"REMEMBER to return json object with these key: {self.keys}"
                )

            count += 1

            try:
                # Wait for the async function with a timeout
                response = await asyncio.wait_for(
                    async_complete_chat(content, self.keys, extra_instructions),
                    timeout=20,
                )
                data.update(json.loads(response.choices[0].message.content))
            except (json.JSONDecodeError, asyncio.TimeoutError) as e:
                logging.error(f"Error or timeout for {link}: {e}")
                continue  # Skip to the next iteration on error or timeout

        print(f"Data: {data}")
        print(f"Updating {link} in database")

        if data:
            update_link_record(
                link_id=id,
                email=data.get("e-mail", ""),
                contact_name=data.get("contact_name", ""),
                industry=data.get("industry", ""),
                city=data.get("city", ""),
                area=data.get("area", ""),
                parsed=1,
            )
        else:
            logging.warning(f"No data for {link}")
            update_link_record(link_id=id, new_parsed=1)

    # TODO After classification, maybe parse the text content?
    async def image_classification(self, id: int, link: str):
        """Classify a image and return a json object"""
        print("Classifying image")
        count = 0
        data = {}

        system_message = {
            "role": "system",
            "content": """
            You are a helpful assistant which purpose is to classify websites on a scale from 1 to 10, where 1 is the lowest and 10 the highest. 
            You are tasked to return two different outputs: a numerical classification from 0 to 10 and a verbose description.
            Classification should be based on the quality of the website: Specifically the look and feel (how well is it designed?), best practices (use of good and large images, CTA-buttons), ui, ux, etc.
            The verbose description should just explain whats in the image
            You should return your response as a json object with the following keys: 'classification' and 'description'
            """,
        }

        # Path to your image
        image_path = f"{self.outfolder}/{link}.png"

        # Getting the base64 string
        base64_image = encode_image(image_path)

        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please classify and describe the following website screenshot",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}",
                        "detail": "high",
                    },
                },
            ],
        }

        while (
            not has_required_keys(json_obj=data, required_keys="classification")
            and count < self.attempts
        ):
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[system_message, user_message],
                    max_tokens=500,
                ),
                timeout=20,
            )

            # Extracting the message content
            message_content = response.choices[0].message.content

            # Stripping the triple backticks and any other non-JSON content
            json_string = message_content.strip("```json\n")

            # Parsing the string to a JSON object
            json_object = json.loads(json_string)

            data.update(json_object)

            print(f"Data: {data}")

            classification = data.get("classification", 0)
            print(f"Updating link with classification: {classification}")
            # Update link return with the classification
            update_link_record(link_id=id, classification=classification)

            if classification <= 6:
                print("Classification less than 6, initializing content parser")
                await self.content_parser(id=id, link=link)

            count += 1

    async def run(self):
        print("Starting AI parser...")
        print(f"There are {len(self.links)} links")
        for id, link in self.links:
            print(f"Parsing {link}")
            await self.image_classification(id=id, link=link)
            break
