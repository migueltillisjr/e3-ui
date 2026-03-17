-- Contacts Table
CREATE TABLE IF NOT EXISTS crm_contacts (
    id TEXT PRIMARY KEY, -- UUID stored as TEXT
    first_name TEXT,
    last_name TEXT,
    email TEXT UNIQUE NOT NULL,
    validated BOOLEAN NOT NULL,
    last_validated TIMESTAMP,
    phone TEXT,
    company TEXT,
    job_title TEXT,
    state TEXT,
    country TEXT,
    city TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_contacted TIMESTAMP,

    -- Lead / Deal / Opportunity Info
    deal_id TEXT,
    deal_value REAL,
    deal_stage TEXT,
    expected_close TIMESTAMP,
    source TEXT,
    status TEXT,

    -- Communication & Interaction
    interaction_type TEXT,
    interaction_date TIMESTAMP,
    notes TEXT,
    follow_up_date TIMESTAMP,

    -- Engagement & Behavior Tracking
    website_visits INTEGER DEFAULT 0,
    email_opens INTEGER DEFAULT 0,
    click_throughs INTEGER DEFAULT 0,
    form_submissions INTEGER DEFAULT 0,

    -- CRM-Specific System Fields
    owner_id TEXT,
    tags TEXT, -- Store as comma-separated or JSON string
    custom_fields TEXT, -- JSON as TEXT
    lifecycle_stage TEXT
);

-- Campaigns Table
CREATE TABLE IF NOT EXISTS crm_campaigns (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))), -- UUID replacement
    name TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'draft',
    created_by TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scheduled_at TIMESTAMP,
    UNIQUE(name)
);

-- Metrics Table
CREATE TABLE IF NOT EXISTS crm_metrics (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))), -- UUID replacement
    campaign_id TEXT NOT NULL,
    send_id TEXT NOT NULL,
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

-- Scheduled Campaigns Table
CREATE TABLE IF NOT EXISTS scheduled_campaigns (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))), -- UUID replacement
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    send_at TIMESTAMP NOT NULL
);
