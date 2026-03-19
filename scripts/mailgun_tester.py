import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
DOMAIN = os.getenv("NEVERBOUNCE_DOMAIN", "e3.hawaiiapsi.org")


def send_simple_message():
    return requests.post(
        f"https://api.mailgun.net/v3/{DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        files={
            "from": (None, f"Mailgun Sandbox <postmaster@{DOMAIN}>"),
            "to": (None, "Miguel Tillis <miguel@infopioneer.ai>"),
            "subject": (None, "Hello Miguel Tillis"),
            "text": (None, "Congratulations Miguel Tillis, you just sent an email with Mailgun!"),
        },
    )


resp = send_simple_message()
print(resp.status_code)
print(resp.text)
