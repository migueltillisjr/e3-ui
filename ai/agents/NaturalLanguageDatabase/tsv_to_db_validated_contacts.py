import os
import sys
import csv
import uuid
from datetime import datetime
from datetime import timezone
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Database config
DB_USER = os.getenv("DB_USER", "nldbpostgres")
DB_PASS = os.getenv("DB_PASS", "nldbpostgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "nldbpostgres")

DATABASE_URL = os.getenv("DB_URL")
engine = create_engine(DATABASE_URL)

EXPECTED_COLUMNS = ['name', 'email', 'valid']




def import_tsv_files():
    dirpath = str(sys.argv[2])
    file_type = str(sys.argv[1]).lower()
    delimiter = '\t' if file_type == "tsv" else ','

    with engine.begin() as conn:
        for file_name in os.listdir(dirpath):
            filepath = os.path.join(dirpath, file_name)
            if not os.path.isfile(filepath):
                continue

            print(f"📂 Processing: {filepath}")

            with open(filepath, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f, fieldnames=EXPECTED_COLUMNS, delimiter=delimiter)
                rows = list(reader)

            for i, row in enumerate(rows):
                email = row.get('email', '').strip()
                if not email or email.lower() == "email":
                    continue  # Skip empty or header rows

                full_name = row.get('name', '').strip()
                first_name, last_name = (full_name.split(" ", 1) + [""])[:2]

                validated = row.get('valid', False)
                validated = validated.lower() in ["true", "1", "yes", "valid"]

                contact = {
                    "id": str(uuid.uuid4()),
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "validated": validated,
                    "created_at": datetime.now(timezone.utc)
                }

                print(f"[{i+1}] {email} -> {contact}")
                sql = """
                INSERT INTO crm_contacts (
                    id, first_name, last_name, email, validated, created_at
                ) VALUES (
                    :id, :first_name, :last_name, :email, :validated, :created_at
                )
                ON CONFLICT (email) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    validated = EXCLUDED.validated;
                """
                conn.execute(text(sql), contact)

            print(f"✅ Finished file: {file_name}")

if __name__ == "__main__":
    import_tsv_files()
