# e3

## Quick Start

```shell
python --version #Python 3.12.3
python -m venv .e3
. .e3/bin/activate
pip install -r requirements.txt
./scripts/data-prep.sh
uvicorn backend:app \
  --host 0.0.0.0 \
  --port 443 \
  --reload \
  --ssl-keyfile=backend/security/private.server.key \
  --ssl-certfile=backend/security/server.crt
```


**Required Integrated Services

- Neverbounce
- MailGun
- Aws Bedrock
- ALB/NLB, with high priority rule exceptions for app context paths
- s3 buckets w/ adequate perms
- Instance profile with access to respective buckets and Bedrock permissions
- 


```shell
#e3-ui % tree -L 2 -I '__pycache__|.git|.pytest_cache|.DS_Store|.e3-ui|node_modules|*.log'
# neverbounce agent
python -m agents.router "validate the first 2 contacts from the united states"
python -m agents.router "Get all contacts"
python -m agents.router "get all contacts with email migueltillisjr@gmail.com"
# mailgun_agent, send
python -m agents.NaturalLanguageEmailer_Mailgun_agent send
# mailgun_agent, metrics
python -m agents.NaturalLanguageEmailer_Mailgun_agent metrics
# nlemaildesigner agent
python -m agents.nlemaildesigner "Add bright colors <h1>visit Hawaii and learn how to teach</h2>"
python -m agents.nlemaildesigner "validate all contacts from Hawaii"
```

### User Pools
- Cognito: https://us-west-1.console.aws.amazon.com/cognito/v2/idp/user-pools/us-west-1_KXIJRIWFQ/applications/app-clients/p4h151ntuikuboridi2austo7/login-pages?region=us-west-1

- Google: https://console.cloud.google.com/auth/clients?project=ampacbusinesscapital

### Frontend - Variable config - frontend/js/global.js
```
const SERVER_ROUTE_PREFIX=`/e3`
const CLIENT_ROUTE_PREFIX=`/e3`
const S3_BUCKET_NAME="e3-designs"
const UI_PORT=443
```

### Backend - Variable config - .env
```shell
UI_PASSWORD=''
UI_USER="e3"
RUN_CMD="uvicorn backend:app --host localhost --port 443 --reload"
APP_UI="http://localhost:443/e3/login"
TAVILY_API_KEY=
AWS_REGION="us-west-2"
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
PORT="443"
DB_USER="nldbpostgres"
DB_PASS="nldbpostgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="nldbpostgres"
DB_URL="sqlite:///backend/storage/database/crm.db"
AWS_ACCOUNT_ID=
MAILGUN_API_KEY=
NEVERBOUNCE_CUSTOM_APP_API_KEY=
NEVERBOUNCE_DOMAIN=
MODEL="us.amazon.nova-pro-v1:0"
PROVIDER="amazon"
SERVER_ROUTE_PREFIX="/e3"
CLIENT_ROUTE_PREFIX="/e3"

LANGSMITH_TRACING="true"
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"
LANGSMITH_API_KEY=
LANGSMITH_PROJECT="e3"

UPLOAD_DIR="backend/storage/serve"
EMAIL_DESIGN_DIR="backend/storage/email_designs"
CONTACTS_DIR="backend/storage/contacts"
METRICS_DIR="backend/storage/metrics"

OAUTH_READ_TIMEOUT=60
OAUTH_CONNECT_TIMEOUT=15
OAUTH_RETRIES=2
COGNITO_DOMAIN=
COGNITO_CLIENT_ID=
COGNITO_CLIENT_SECRET=
COGNITO_POOL_ID=
COGNITO_SERVER_METADATA_URL=
COGNITO_REDIRECT_URI="http://localhost:443/auth/callback"
COGNITO_REGION="us-west-1"
CORS_ALLOWED_ORIGINS="*"
FASTAPI_SECRET_KEY=super-secret-fastapi-key
BASE_URL=http://localhost:443
VITE_WS_API_ID=
VITE_AWS_REGION=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_AUTH_REDIRECT_URI=
GOOGLE_OAUTH_METADATA_URL=""
```


### Setup Ai
ai/README.ai.md

### Setup API
api/README.api.md

### Setup UiUx
api/README.uiux.md



### Production deploy

- transfer e3-main.zip to server
- update auth variables in PROJECT_ROOT/.env
- open port 443
- setup nlb and alb
- create target group to port 443 to ec2 instance
- add ALB rule to alb to point to ec2 instance target group, route /e3, OR /e3/*
- modify the ALB common ruleset for the ACL associated with respective ALB WAF, change max body size rule to allow
- create app user sudo useradd --system --no-create-home --shell /usr/sbin/nologin e3
- create service file
- sudo chown -R e3:e3 .e3/
- make env dir writeable 777 .e3/
```
[Unit]
Description=My Python API Service
After=network.target

[Service]
Type=simple
User=e3
WorkingDirectory=/opt/e3
ExecStart=/bin/bash -c 'source /opt/.e3/bin/activate && python -m api'
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

