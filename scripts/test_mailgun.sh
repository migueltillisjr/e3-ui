#!/bin/bash
# Quick curl-based Mailgun send test — pulls creds from .env

set -euo pipefail

API_KEY=$(grep '^MAILGUN_API_KEY=' .env | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d ' ')
DOMAIN=$(grep '^NEVERBOUNCE_DOMAIN=' .env | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d ' ')

if [ -z "$API_KEY" ] || [ -z "$DOMAIN" ]; then
  echo "Missing MAILGUN_API_KEY or NEVERBOUNCE_DOMAIN in .env"
  exit 1
fi

read -p "Send to (email): " TO_EMAIL

curl -s --user "api:${API_KEY}" \
  "https://api.mailgun.net/v3/${DOMAIN}/messages" \
  -F "from=Excited User <postmaster@${DOMAIN}>" \
  -F "to=${TO_EMAIL}" \
  -F "subject=Hello there!" \
  -F "text=Testing some Mailgun awesomeness!"
