CREATE TABLE crm_contacts (
    id TEXT PRIMARY KEY,
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
    deal_value FLOAT,
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
    tags TEXT[], -- PostgreSQL array of TEXT
    custom_fields TEXT,
    lifecycle_stage TEXT
);


CREATE TABLE IF NOT EXISTS crm_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    description TEXT,
    status VARCHAR DEFAULT 'draft',
    created_by UUID,
    created_at TIMESTAMP DEFAULT now(),
    scheduled_at TIMESTAMP,
    CONSTRAINT uq_campaign_name UNIQUE (name)
);

CREATE TABLE IF NOT EXISTS crm_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES crm_campaigns(id) ON DELETE CASCADE,
    send_id UUID NOT NULL, -- Optional tracking of each send operation
    sent_at TIMESTAMP DEFAULT now(),

    total_sent INTEGER DEFAULT 0,
    total_opened INTEGER DEFAULT 0,
    total_clicked INTEGER DEFAULT 0,
    total_bounced INTEGER DEFAULT 0,
    total_unsubscribed INTEGER DEFAULT 0,

    open_rate FLOAT,
    click_through_rate FLOAT,
    bounce_rate FLOAT,
    unsubscribe_rate FLOAT
);

CREATE TABLE IF NOT EXISTS scheduled_campaigns (
    id UUID PRIMARY KEY,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    send_at TIMESTAMP NOT NULL
);
