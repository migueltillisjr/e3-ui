# E3 — AI-Powered Email Marketing Platform

Contact management, email design, campaign delivery, and email validation — all driven by natural language through AI agents.

## What's Inside

| Component | Description |
|-----------|-------------|
| `.opencode/` | Opencode agent settings |
| `backend/` | FastAPI app — API routes, OAuth (Cognito + Google), Pydantic models |
| `frontend/` | Vanilla JS + CKEditor email editor UI |
| `agents/` | LangChain AI agents (NL→SQL, NeverBounce, Mailgun, HTML design) |
| `storage/` | Runtime data — SQLite DB, contacts, email designs, metrics |
| `cicd/` | Deployment pipeline and config |
| `scripts/` | Dev/ops utilities |

## Prerequisites

- Python 3.12+
- API keys for: AWS Bedrock, Mailgun, NeverBounce
- SSL cert + key in `backend/security/`

## Quick Start

```shell
# 1. Create and activate virtual environment
python -m venv .e3
source .e3/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp env.example .env
# Edit .env with your API keys and config

# 4. Initialize the database
./scripts/data-prep.sh

# 5. Start the server
uvicorn backend:app \
  --host 0.0.0.0 \
  --port 443 \
  --reload \
  --ssl-keyfile=backend/security/private.server.key \
  --ssl-certfile=backend/security/server.crt
```

The app will be available at `https://localhost:443/e3/`

## Using the AI Agents (CLI)

All agents are accessed through the router via natural language:

```shell
# Query contacts
python -m agents.router "Get all contacts from Hawaii"

# Validate emails via NeverBounce
python -m agents.router "validate the first 2 contacts from the united states"

# Edit HTML email snippets
python -m agents.router "Add bright colors <h1>visit Hawaii</h1>"
```

Direct agent access:

```shell
# Send an email campaign
python -m agents.NaturalLanguageEmailer_Mailgun_agent send

# View email delivery metrics
python -m agents.NaturalLanguageEmailer_Mailgun_agent metrics
```

## Environment Variables

Copy `env.example` to `.env` and fill in the values. Key groups:

| Group | Variables |
|-------|-----------|
| AWS / Bedrock | `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_ACCOUNT_ID`, `MODEL`, `PROVIDER` |
| Mailgun | `MAILGUN_API_KEY`, `NEVERBOUNCE_DOMAIN` |
| NeverBounce | `NEVERBOUNCE_CUSTOM_APP_API_KEY` |
| Database | `DB_URL` (default: `sqlite:///backend/storage/database/crm.db`) |
| Auth — Cognito | `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET`, `COGNITO_POOL_ID`, `COGNITO_REDIRECT_URI` |
| Auth — Google | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_AUTH_REDIRECT_URI` |
| Routing | `SERVER_ROUTE_PREFIX` (default: `/e3`), `CLIENT_ROUTE_PREFIX` |
| Storage paths | `UPLOAD_DIR`, `EMAIL_DESIGN_DIR`, `CONTACTS_DIR`, `METRICS_DIR` |

## Frontend Config

Edit `frontend/js/global.js`:

```js
const SERVER_ROUTE_PREFIX = `/e3`
const CLIENT_ROUTE_PREFIX = `/e3`
const S3_BUCKET_NAME = "e3-designs"
const UI_PORT = 443
```

## Production Deployment

The `cicd/` directory handles automated deployment. For manual setup:

1. Transfer release archive to server
2. Configure `.env` with production values
3. Create a system user:
   ```shell
   sudo useradd --system --no-create-home --shell /usr/sbin/nologin e3
   ```
4. Set up the virtual environment and permissions:
   ```shell
   sudo chown -R e3:e3 .e3/
   ```
5. Install the systemd service (see `uvicorn.service`)
6. Configure networking:
   - Open port 443
   - Set up ALB/NLB with target group pointing to the EC2 instance
   - Add ALB rule for `/e3` and `/e3/*`
   - Update WAF ACL max body size rule if needed

## Project Documentation

- `AGENTS.md` — Agent routing and project structure
- `CONTEXT.md` — Project context and goals
- `CHANGELOG.md` — Release history
- Each agent directory has its own `CONTEXT.md`

## OpenCode Agent

The project includes an [OpenCode](https://opencode.ai) agent config at `.opencode/agents/e3.md`. It gives OpenCode project-aware context so it understands the agent structure, symlinks, and conventions when you use it for development.

- Model: `us.amazon.nova-pro-v1:0`
- Mode: subagent
- Tools: write, bash

The agent is pre-configured to read `AGENTS.md` and per-agent `CONTEXT.md` files before making changes.
