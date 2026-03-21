"""Quick Mailgun send test — uses MAILGUN_API_KEY and NEVERBOUNCE_DOMAIN from .env"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MAILGUN_API_KEY")
DOMAIN = os.getenv("NEVERBOUNCE_DOMAIN")

if not API_KEY or not DOMAIN:
    raise SystemExit("Missing MAILGUN_API_KEY or NEVERBOUNCE_DOMAIN in .env")

TO_EMAIL = input("Send to (email): ").strip()

resp = requests.post(
    f"https://api.mailgun.net/v3/{DOMAIN}/messages",
    auth=("api", API_KEY),
    data={
        "from": f"Test <mailgun@{DOMAIN}>",
        "to": [TO_EMAIL],
        "subject": "Mailgun Test",
        "text": "If you're reading this, Mailgun is working.",
    },
)

print(f"[{resp.status_code}] {resp.text}")
