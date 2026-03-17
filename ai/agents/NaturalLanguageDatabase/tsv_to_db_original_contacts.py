import os
import sys
import csv
import uuid
from datetime import datetime
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

import os

cwd = os.getcwd()
print(cwd)

TSV_DIRECTORY = f'{cwd}/ai/test_data/master_contact_lists'



def import_tsv_files(TSV_DIRECTORY: str = TSV_DIRECTORY):

    with engine.begin() as conn:
        print(f"Processing {TSV_DIRECTORY}/27k-export - E3-export.tsv")
        with open(TSV_DIRECTORY + "/27k-export - E3-export.tsv", newline='', encoding='utf-8') as tsvfile:
            reader = csv.DictReader(tsvfile, delimiter='\t')
            for row in reader:
                row = {k.lower(): v for k, v in row.items()}

                full_name = row.get("name", "").strip()
                first_name, last_name = (full_name.split(" ", 1) + [""])[:2]

                validated_raw = row.get("validated", "").strip().lower()
                validated = validated_raw in ["true", "1", "yes"]

                contact_dict = {
                    "id": str(uuid.uuid4()),
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": row.get("email", "").strip(),
                    "validated": validated,
                    "city": row.get('city', ''),
                    "state": row.get('state', ''),
                    "country": row.get('country', ''),
                    "created_at": datetime.utcnow()
                }

                sql = """
                INSERT INTO crm_contacts (
                    id, first_name, last_name, email, validated, city, state, country, created_at
                ) VALUES (
                    :id, :first_name, :last_name, :email, :validated, :city, :state, :country, :created_at
                )
                ON CONFLICT (email) DO NOTHING;
                """
                conn.execute(text(sql), contact_dict)

        print("✅ All contacts imported.")


if __name__ == "__main__":
    filepath = str(sys.argv[1])
    import_tsv_files()
