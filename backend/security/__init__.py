from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi import HTTPException
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from ai.agents.router import route_ai_request
from ai.agents.aws_agent import upload_html_design_to_bucket
from ai.agents.NaturalLanguageEmailer_Mailgun.entrypoint import initiate_email_send
from ai.agents.NaturalLanguageEmailer_Mailgun import get_metrics
import uvicorn
import os
import re
from uuid import uuid4
from datetime import datetime
import json
from pathlib import Path
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime
from urllib.parse import urlparse
from typing import List
import uuid
import pandas as pd
import csv
# db.py
import io
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
from typing import Any, Dict
import dotenv
import httpx
import jwt
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from fastapi import APIRouter, Depends
from fastapi import HTTPException, Request, status
from backend import *
import os
import httpx
from authlib.integrations.starlette_client import OAuth
from authlib.integrations.httpx_client import AsyncOAuth2Client

dotenv.load_dotenv()

OAUTH_READ_TIMEOUT  = float(os.getenv("OAUTH_READ_TIMEOUT",  60))  # seconds
OAUTH_CONNECT_TIMEOUT = float(os.getenv("OAUTH_CONNECT_TIMEOUT", 15))
OAUTH_RETRIES = int(os.getenv("OAUTH_RETRIES", 2))

SERVER_ROUTE_PREFIX=os.getenv("SERVER_ROUTE_PREFIX")
CLIENT_ROUTE_PREFIX=os.getenv("CLIENT_ROUTE_PREFIX")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR")) #"uploaded_images"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR = Path(os.getenv("UPLOAD_DIR") + "/uploaded_images") #"uploaded_images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)
EMAIL_DESIGN_DIR = Path(os.getenv("EMAIL_DESIGN_DIR")) # email_designs
EMAIL_DESIGN_DIR.mkdir(parents=True, exist_ok=True)
CONTACTS_DIR = Path(os.getenv("CONTACTS_DIR")) # contacts
CONTACTS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR = Path(os.getenv("METRICS_DIR")) # metrics
METRICS_DIR.mkdir(parents=True, exist_ok=True)
# ---------------------------------------------
# Load env FIRST
# ---------------------------------------------

# ---------------- SESSION-BASED AUTH ----------------
def get_current_user(request: Request) -> Dict[str, Any]:
    """Checks if the user is logged in via session."""
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

# Create a router with an automatic dependency on authentication
protected_router = APIRouter(
    prefix="/user",  # All routes will be under /user
    tags=["protected"],
    dependencies=[Depends(get_current_user)]
)


# ---------------------------------------------
# Base config
# ---------------------------------------------
SECRET_KEY = os.getenv("FASTAPI_SECRET_KEY", "a-very-secret-key")

TEST_USERNAME = os.getenv("TEST_USERNAME", "test@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "test-password")

# Useful if your app sits behind a reverse proxy with a public URL
BASE_EXTERNAL_URL = os.getenv("BASE_EXTERNAL_URL", "https://localhost:443")

# ---------------------------------------------
# AWS Cognito config
# ---------------------------------------------
COGNITO_REGION = os.getenv("COGNITO_REGION", "us-west-1")
COGNITO_POOL_ID = os.getenv("COGNITO_POOL_ID", "us-west-1_DPeMWoTJY")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID", "")
COGNITO_CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET", "")
COGNITO_SERVER_METADATA_URL = os.getenv("COGNITO_SERVER_METADATA_URL", f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}/.well-known/openid-configuration")
# Avoid 0.0.0.0 here; use localhost or your domain
COGNITO_REDIRECT_URI = os.getenv(
    "COGNITO_REDIRECT_URI",
    f"{BASE_EXTERNAL_URL}/auth/cognito/callback"
)
COGNITO_ISSUER = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_POOL_ID}"
COGNITO_WELL_KNOWN = f"{COGNITO_ISSUER}/.well-known/openid-configuration"
JWKS_URL = f"{COGNITO_ISSUER}/.well-known/jwks.json"

# ---------------------------------------------
# Google config
# ---------------------------------------------
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_OAUTH_METADATA_URL = os.getenv("GOOGLE_OAUTH_METADATA_URL", "")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI",
    f"{BASE_EXTERNAL_URL}/auth/google/callback"
)

# ---------------------------------------------
# FastAPI app + session
# ---------------------------------------------
# # Initialize FastAPI app
app = FastAPI(docs_url="/docs", openapi_url="/openapi.json")
# 🗂 Mount static directories for CSS/JS/assets
app.mount(f"{SERVER_ROUTE_PREFIX}/css", StaticFiles(directory="frontend/css"), name="css")
app.mount(f"{SERVER_ROUTE_PREFIX}/js", StaticFiles(directory="frontend/js"), name="js")
app.mount(f"{SERVER_ROUTE_PREFIX}/images", StaticFiles(directory=str(IMAGE_DIR)), name="images")
client = TestClient(app)

# For local dev:
# - same_site="lax" works for standard redirects on same site
# In production behind HTTPS + cross-site, consider same_site="none", https_only=True
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=False,
)
# # Enable CORS if needed
# app.add_middleware(
#     CORSMiddleware,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     same_site="lax",
#     https_only=False
# )


# ---------------------------------------------
# OAuth setup
# ---------------------------------------------
oauth = OAuth()


common_client_kwargs = {
    # Increase timeouts (connect/read/write/pool)
    "timeout": httpx.Timeout(
        connect=OAUTH_CONNECT_TIMEOUT,
        read=OAUTH_READ_TIMEOUT,
        write=OAUTH_READ_TIMEOUT,
        pool=OAUTH_READ_TIMEOUT,
    ),
    # Optional: light retry on transient network errors
    "transport": httpx.AsyncHTTPTransport(retries=OAUTH_RETRIES),
    # Optional: headers, proxies, etc. can go here too
    # "headers": {"User-Agent": "e3/1.0"},
}

oauth.register(
    name='oidc',
    client_id=COGNITO_CLIENT_ID,
    client_secret=COGNITO_CLIENT_SECRET,
    server_metadata_url=COGNITO_SERVER_METADATA_URL,
    # client_kwargs={'scope': 'phone openid email'}
    client_kwargs={
        "scope": "phone openid email",
        **common_client_kwargs,
    }
)

# Register Google (OIDC)
oauth.register(
    name="google",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url=GOOGLE_OAUTH_METADATA_URL,
    # client_kwargs={"scope": "openid email profile"},
    client_kwargs={
        "scope": "openid email profile",
        **common_client_kwargs,
    }
    # token_endpoint_auth_method="client_secret_post",  # Uncomment if you get invalid_client at token step
)

# ---------------------------------------------
# Optional: JWKS cache for manual token validation (Cognito)
# ---------------------------------------------
_jwks_cache: Dict[str, Any] | None = None

async def get_jwks() -> Dict[str, Any]:
    global _jwks_cache
    if not _jwks_cache:
        async with httpx.AsyncClient() as client:
            resp = await client.get(JWKS_URL, timeout=10)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache

async def validate_token(id_token: str) -> Dict[str, Any]:
    """Validate and decode a Cognito JWT ID token."""
    jwks = await get_jwks()
    headers = jwt.get_unverified_header(id_token)
    key = next((k for k in jwks["keys"] if k["kid"] == headers.get("kid")), None)
    if not key:
        raise HTTPException(status_code=401, detail="Invalid token key ID")

    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key))
    try:
        payload = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
            options={"verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    return payload