#!/bin/bash

python -m ai.agents.NaturalLanguageEmailer_Mailgun_agent send 
# "$(cat <<EOF
# {
#   "design_name": "email_design1.html",
#   "html_email_design": "https://e3-designs.s3.amazonaws.com/email_design1.html",
#   "subject": "This is a test!",
#   "preview": "This is a test!",
#   "from_data": "Jennie < jennie@e3.hawaiiapsi.org >",
#   "tracking": "yes",
#   "send_date": "2025-09-01"
# }
# EOF
# )"