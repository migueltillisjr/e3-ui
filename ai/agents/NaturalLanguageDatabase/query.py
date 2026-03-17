import os
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


def query_first_ten():
    sql = """
    SELECT first_name, last_name, email, validated 
    FROM crm_contacts 
    LIMIT 10;
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        for row in result:
            print(row)
            print(f"{row.first_name} {row.last_name} - {row.email} - Validated: {row.validated}")


def query_validated():
    sql = """
    SELECT first_name, last_name, email, validated 
    FROM crm_contacts 
    WHERE validated = TRUE 
    LIMIT 10;
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        for row in result:
            print(row)
            print(f"{row.first_name} {row.last_name} - {row.email} - Validated: {row.validated}")
        conn.commit()


if __name__ == "__main__":
    # query_first_ten()
    query_validated()
