import os
import requests
from datetime import datetime, timedelta, timezone
import random

api_key = os.getenv("MAILGUN_KEY")


# Function to generate a random time between 10:00 and 11:30 in GMT+1 in RFC-2822 format
def get_random_time_rfc2822():
    # Define a base date
    base_date = datetime.now().date()

    # Define the start and end times in the GMT+1 timezone
    start_time = datetime.combine(base_date, datetime.min.time()) + timedelta(
        hours=10
    )  # 10:00 GMT+1
    end_time = start_time + timedelta(hours=1, minutes=30)  # 11:30 GMT+1

    # Calculate a random time between start_time and end_time
    random_time_in_seconds = random.randint(
        0, int((end_time - start_time).total_seconds())
    )
    random_time = start_time + timedelta(seconds=random_time_in_seconds)

    # Format the random time according to RFC-2822, with the correct timezone for GMT+1
    formatted_time = random_time.strftime("%a, %d %b %Y %H:%M:%S +0100")
    return formatted_time


def schedule_email(domain, from_email, to_email, subject, text):
    deliverytime = get_random_time_rfc2822()

    return requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": from_email,
            "to": to_email,
            "subject": f"{subject}: {deliverytime}",
            "text": text,
            "o:tracking": True,
            "o:tracking-opens": True,
            "o:deliverytime": deliverytime,
        },
    )
