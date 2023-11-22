import os
import requests
import pytz
from datetime import datetime, timedelta
import random

from database import get_next_email_event_date

api_key = os.getenv("MAILGUN_KEY")
emails = os.getenv("EMAILS").split(",")
sender_name = os.getenv("SENDER_NAME")


from datetime import datetime, timedelta, date
import pytz
import random

def get_random_time_rfc2822(date_str):
    # Define the timezone for GMT+1
    timezone = pytz.timezone("Etc/GMT-1")

    # Check if date_str is a string and parse it, otherwise use it directly if it's a date object
    if isinstance(date_str, str):
        try:
            base_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
    elif isinstance(date_str, date):
        base_date = date_str
    else:
        raise TypeError("date_str must be a string or datetime.date")

    # Define the start and end times in the GMT+1 timezone
    start_time = datetime.combine(base_date, datetime.min.time(), timezone) + timedelta(hours=10)
    end_time = start_time + timedelta(hours=1, minutes=30)

    # Calculate a random time between start_time and end_time
    random_time_in_seconds = random.randint(0, int((end_time - start_time).total_seconds()))
    random_time = start_time + timedelta(seconds=random_time_in_seconds)

    # Format the random time according to RFC-2822
    formatted_time = random_time.strftime("%a, %d %b %Y %H:%M:%S %z")
    return formatted_time



def schedule_email(to_email, subject, text):
    next_email_event_date = get_next_email_event_date()

    deliverytime = get_random_time_rfc2822(date_str=next_email_event_date)

    from_email = random.choice(emails)

    domain = from_email.split("@")[-1]

    mailgun_request = requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={
            "from": f"{sender_name} <{from_email}>",
            "to": to_email,
            "subject": {subject},
            "text": text,
            "o:tracking": True,
            "o:tracking-opens": True,
            "o:deliverytime": deliverytime,
        },
    )

    if mailgun_request.status_code != 200:
        raise Exception(mailgun_request.text)
    
    return deliverytime
