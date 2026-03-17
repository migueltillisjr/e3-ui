#!/bin/bash

echo "Deleting existing contacts files.."
rm backend/storage/contacts/*

# echo "Deleting existing container..."
# docker rm e3nldbpostgres --force

# echo "Deploy Postgress..."
# docker compose up -d

# echo "Waiting for DB creation..."
# sleep 10

echo "Creating schema..."
python "$PWD/ai/agents/NaturalLanguageDatabase/initializedb.py" > /dev/null

echo "Loading original all contacts..."
python $PWD/ai/agents/NaturalLanguageDatabase/tsv_to_db_original_contacts.py \
"$PWD/ai/test_data/master_contact_lists/27k-export - E3-export.tsv" > /dev/null

echo "Importing validated contacts..."
python ai/agents/NaturalLanguageDatabase/tsv_to_db_validated_contacts.py tsv \
"$PWD/ai/test_data/prod/dbload_validated/tsv" > /dev/null
python ai/agents/NaturalLanguageDatabase/tsv_to_db_validated_contacts.py csv \
"$PWD/ai/test_data/prod/dbload_validated/csv" > /dev/null

echo "Validating responses come back from nldb..."
python "$PWD/ai/agents/NaturalLanguageDatabase/query.py"

echo "nldb query + TSV file generation..."
python -m ai.agents.NaturalLanguageDatabase "return all validated contacts"
ls -la "$PWD/backend/storage/contacts/contacts.tsv"

# echo "Validating email send..."
# python -m ai.agents.NaturalLanguageEmailer_Mailgun_agent send "$(cat <<EOF
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

echo "Validating metrics grab..."
python -m ai.agents.NaturalLanguageEmailer_Mailgun metrics
ls -la "$PWD/backend/storage/metrics/email_metrics_current.png"

echo "Starting email validation..."
echo "Gather contacts subset to validate..."
python -m ai.agents.NaturalLanguageDatabase "return contact with email kyle.weir@stonehill.in that is not valid"
ls -la "$PWD/backend/storage/contacts/contacts.tsv"

echo "Initiate email validation..."
python -m ai.agents.neverbounce "validate the top 1 invalid contacts"

echo "validate new db entry with validated status..."
# PGPASSWORD='nldbpostgres' psql -U nldbpostgres -d nldbpostgres -h localhost -p 5432 \
# -t -A -c "SELECT row_to_json(crm_contacts) FROM crm_contacts WHERE email = 'migueltillisjr@gmail.com';"
python -c 'import sqlite3, json; 
conn = sqlite3.connect("backend/storage/database/crm.db"); 
conn.row_factory = sqlite3.Row; 
row = conn.execute("SELECT * FROM crm_contacts WHERE email = ?", ("migueltillisjr@gmail.com",)).fetchone(); 
print(json.dumps(dict(row)) if row else "{}")'


echo "Validating that the invalid contact was removed from DB..."
# result=$(PGPASSWORD='nldbpostgres' psql -U nldbpostgres -d nldbpostgres -h localhost -p 5432 \
#   -t -A -c "SELECT row_to_json(crm_contacts) FROM crm_contacts WHERE email = 'christopher.poznanski@csd15.net';")

python -c 'import sqlite3, json; 
conn = sqlite3.connect("backend/storage/database/crm.db"); 
conn.row_factory = sqlite3.Row; 
row = conn.execute("SELECT * FROM crm_contacts WHERE email = ?", ("christopher.poznanski@csd15.net",)).fetchone(); 
print(json.dumps(dict(row)) if row else "{}")'


if [[ -z "$result" ]]; then
  echo "✅ Invalid contact successfully removed from the database."
else
  echo "❌ Contact still exists in the database:"
  echo "$result"
fi
