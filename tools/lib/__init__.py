# Shared config and helpers for CLI tools
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")
SERVER_ROUTE_PREFIX = os.getenv("SERVER_ROUTE_PREFIX", "/e3")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "storage/serve")
EMAIL_DESIGN_DIR = os.getenv("EMAIL_DESIGN_DIR", "storage/email_designs")
CONTACTS_DIR = os.getenv("CONTACTS_DIR", "storage/contacts")
METRICS_DIR = os.getenv("METRICS_DIR", "storage/metrics")

# Ensure directories exist
for d in [UPLOAD_DIR, EMAIL_DESIGN_DIR, CONTACTS_DIR, METRICS_DIR]:
    Path(d).mkdir(parents=True, exist_ok=True)

engine = None
if DATABASE_URL:
    kwargs = {}
    if "sqlite" in DATABASE_URL:
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(DATABASE_URL, **kwargs)
