from sqlalchemy import create_engine
from sqlalchemy import text
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "nldbpostgres")
DB_PASS = os.getenv("DB_PASS", "nldbpostgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "nldbpostgres")

DATABASE_URL = os.getenv("DB_URL")

engine = create_engine(DATABASE_URL)

def load_schema_crm_contacts():
    with engine.connect() as conn:
        # postgresql requirement
        # conn.execute(text("""
        # CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        # """))

        # conn.execute(text("""
        # CREATE TABLE IF NOT EXISTS crm_contacts (
        #     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        #     first_name VARCHAR,
        #     last_name VARCHAR,
        #     email VARCHAR NOT NULL,
        #     validated BOOLEAN DEFAULT FALSE NOT NULL,
        #     last_validated TIMESTAMP,
        #     phone VARCHAR,
        #     company VARCHAR,
        #     job_title VARCHAR,
        #     state VARCHAR,
        #     country VARCHAR,
        #     city VARCHAR,
        #     created_at TIMESTAMP DEFAULT now(),
        #     last_contacted TIMESTAMP,
        #     deal_id UUID,
        #     deal_value FLOAT,
        #     deal_stage VARCHAR,
        #     expected_close TIMESTAMP,
        #     source VARCHAR,
        #     status VARCHAR,
        #     interaction_type VARCHAR,
        #     interaction_date TIMESTAMP,
        #     notes TEXT,
        #     follow_up_date TIMESTAMP,
        #     website_visits INTEGER DEFAULT 0,
        #     email_opens INTEGER DEFAULT 0,
        #     click_throughs INTEGER DEFAULT 0,
        #     form_submissions INTEGER DEFAULT 0,
        #     owner_id UUID,
        #     tags TEXT[],
        #     custom_fields JSONB,
        #     lifecycle_stage VARCHAR,
        #     CONSTRAINT uq_email UNIQUE (email)
        # );
        # """))
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS crm_contacts (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))), -- UUID replacement
            first_name TEXT,
            last_name TEXT,
            email TEXT NOT NULL,
            validated BOOLEAN DEFAULT FALSE NOT NULL,
            last_validated TIMESTAMP,
            phone TEXT,
            company TEXT,
            job_title TEXT,
            state TEXT,
            country TEXT,
            city TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contacted TIMESTAMP,
            deal_id TEXT, -- UUID as TEXT
            deal_value REAL,
            deal_stage TEXT,
            expected_close TIMESTAMP,
            source TEXT,
            status TEXT,
            interaction_type TEXT,
            interaction_date TIMESTAMP,
            notes TEXT,
            follow_up_date TIMESTAMP,
            website_visits INTEGER DEFAULT 0,
            email_opens INTEGER DEFAULT 0,
            click_throughs INTEGER DEFAULT 0,
            form_submissions INTEGER DEFAULT 0,
            owner_id TEXT, -- UUID as TEXT
            tags TEXT, -- Use comma-separated string or JSON text
            custom_fields TEXT, -- Store JSON as text
            lifecycle_stage TEXT,
            UNIQUE(email)
        );

        """))

        conn.commit()

        # Continue similarly for other tables...

        print("Schema created successfully.")


def load_schema_crm_campaigns():
    with engine.connect() as conn:
        # conn.execute(text("""
        # CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        # """))

        # conn.execute(text("""
        # CREATE TABLE IF NOT EXISTS crm_campaigns (
        #     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        #     name VARCHAR NOT NULL,
        #     description TEXT,
        #     status VARCHAR DEFAULT 'draft',
        #     created_by UUID,
        #     created_at TIMESTAMP DEFAULT now(),
        #     scheduled_at TIMESTAMP,
        #     CONSTRAINT uq_campaign_name UNIQUE (name)
        # );
        # """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS crm_campaigns (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))), -- UUID fallback
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'draft',
            created_by TEXT, -- UUID as TEXT
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_at TIMESTAMP,
            UNIQUE(name)
        );

        """))
        conn.commit()

        # Continue similarly for other tables...

        print("Schema created successfully.")

def load_schema_crm_metrics():
    with engine.connect() as conn:
        # conn.execute(text("""
        # CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        # """))

        # conn.execute(text("""
        # CREATE TABLE IF NOT EXISTS crm_metrics (
        #     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        #     campaign_id UUID NOT NULL REFERENCES crm_campaigns(id) ON DELETE CASCADE,
        #     send_id UUID NOT NULL, -- Optional tracking of each send operation
        #     sent_at TIMESTAMP DEFAULT now(),

        #     total_sent INTEGER DEFAULT 0,
        #     total_opened INTEGER DEFAULT 0,
        #     total_clicked INTEGER DEFAULT 0,
        #     total_bounced INTEGER DEFAULT 0,
        #     total_unsubscribed INTEGER DEFAULT 0,

        #     open_rate FLOAT,
        #     click_through_rate FLOAT,
        #     bounce_rate FLOAT,
        #     unsubscribe_rate FLOAT
        # );
        # """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS crm_metrics (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))), -- UUID fallback
            campaign_id TEXT NOT NULL, -- UUID as TEXT
            send_id TEXT NOT NULL,     -- UUID as TEXT
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            total_sent INTEGER DEFAULT 0,
            total_opened INTEGER DEFAULT 0,
            total_clicked INTEGER DEFAULT 0,
            total_bounced INTEGER DEFAULT 0,
            total_unsubscribed INTEGER DEFAULT 0,

            open_rate REAL,
            click_through_rate REAL,
            bounce_rate REAL,
            unsubscribe_rate REAL,

            FOREIGN KEY (campaign_id) REFERENCES crm_campaigns(id) ON DELETE CASCADE
        );

        """))

        conn.commit()

        # Continue similarly for other tables...

        print("Schema created successfully.")


def load_schema_crm_scheduled_campaigns():
    with engine.connect() as conn:
        # conn.execute(text("""
        # CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        # """))

        # conn.execute(text("""
        # CREATE TABLE IF NOT EXISTS scheduled_campaigns (
        #     id UUID PRIMARY KEY,
        #     recipient TEXT NOT NULL,
        #     subject TEXT NOT NULL,
        #     body TEXT NOT NULL,
        #     send_at TIMESTAMP NOT NULL
        # );
        # """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS scheduled_campaigns (
            id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))), -- UUID fallback
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            send_at TIMESTAMP NOT NULL
        );

        """))

        conn.commit()

        # Continue similarly for other tables...

        print("Schema created successfully.")

load_schema_crm_contacts()
load_schema_crm_campaigns()
load_schema_crm_metrics()
load_schema_crm_scheduled_campaigns()


