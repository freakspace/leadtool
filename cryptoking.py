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


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


class AiParser:
    def __init__(self):
        self.screenshots = ["ethtest.jpg"]
        self.attempts = 1

    async def image_classification(self, screenshot: str):
        """Classify a image and return a json object"""
        print("Analysing image")
        data = {}

        system_message = {
            "role": "system",
            "content": """
            You are a an extremely talented trader with more than 20 years of experience with technical analysis. 
            Your task is to analyse a given screenshot of an asset, and determine if you expect it to increase or descrease in value.
            """,
        }

        # Path to your image
        image_path = f"content/{screenshot}"

        # Getting the base64 string
        base64_image = encode_image(image_path)

        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please analyse the following screenshot",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpg;base64,{base64_image}",
                        "detail": "high",
                    },
                },
            ],
        }

        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[system_message, user_message],
                max_tokens=500,
            ),
            timeout=20,
        )

        # Extracting the message content
        analysis = response.choices[0].message.content

        # print(message_content)
        # Stripping the triple backticks and any other non-JSON content
        # json_string = message_content.strip("```json\n")

        # Parsing the string to a JSON object
        # json_object = json.loads(json_string)

        # data.update(json_object)

        return analysis

    async def run(self):
        print("Starting AI parser...")
        for screenshot in self.screenshots:
            print(f"Parsing {screenshot}")
            data = await self.image_classification(screenshot=screenshot)
            print(data)


async def main():
    king = AiParser()
    await king.run()


if __name__ == "__main__":
    asyncio.run(main())
