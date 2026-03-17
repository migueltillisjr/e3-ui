
# from .security import *
from .route_models import *
from .security import *
from string import Template
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request, Query, Body
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
from ai.agents.NaturalLanguageDatabase.tsv_to_db_original_contacts import import_tsv_files
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



# Load .env variables
load_dotenv()

DB_USER = os.getenv("DB_USER", "nldbpostgres")
DB_PASS = os.getenv("DB_PASS", "nldbpostgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "nldbpostgres")
PORT = os.getenv("PORT", "443")
DATABASE_URL = os.getenv("DB_URL") #or f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = object()

if 'postgresql' in DATABASE_URL:
    engine = create_engine(DATABASE_URL)
if 'sqlite' in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})



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

UPLOAD_DIR = str(UPLOAD_DIR)
IMAGE_DIR = str(IMAGE_DIR)
EMAIL_DESIGN_DIR = str(EMAIL_DESIGN_DIR)
CONTACTS_DIR = str(CONTACTS_DIR)
METRICS_DIR = str(METRICS_DIR)



# Set up the templates directory
html_path = os.path.abspath("frontend/")
templates = Jinja2Templates(directory=html_path)


# ---------------------------------------------
# Routes
# ---------------------------------------------
@app.get(f"{SERVER_ROUTE_PREFIX}/health/ping")
async def health_check(request: Request):
    return {"message": f"<h1>Healthy!</h1>"}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user")
    if user:
        email = user.get("email") or user.get("preferred_username") or "User"
        sub = user.get("sub")
        email_verified = user.get("email_verified")
        user_name = user.get("username")
        return RedirectResponse(url=f"{SERVER_ROUTE_PREFIX}/")
    return Template("""
    <html>
    <head>
        <title>Login</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #ece9e6, #ffffff);
                height: 100vh;
                margin: 0;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: white;
                padding: 2rem 3rem;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
                max-width: 400px;
                width: 100%;
            }
            h1 {
                margin-bottom: 1rem;
                color: #333;
            }
            .login-btn {
                display: block;
                width: 100%;
                margin: 0.5rem 0;
                padding: 0.75rem;
                border-radius: 5px;
                font-size: 1rem;
                font-weight: bold;
                border: none;
                cursor: pointer;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }
            .login-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            .cognito {
                background-color: #2f80ed;
                color: white;
            }
            .google {
                background-color: white;
                color: #555;
                border: 1px solid #ccc;
            }
            .google img {
                height: 20px;
                vertical-align: middle;
                margin-right: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome!</h1>
            <p>Please choose a login method:</p>
            <a href="$SERVER_ROUTE_PREFIX/login">
                <button class="login-btn cognito">🔐 Login</button>
            </a>
            <a href="$SERVER_ROUTE_PREFIX/login/google">
                <button class="login-btn google">
                    <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google logo">
                    Login with Google
                </button>
            </a>
        </div>
    </body>
    </html>
    """).substitute(SERVER_ROUTE_PREFIX=SERVER_ROUTE_PREFIX)


@app.get(f"{SERVER_ROUTE_PREFIX}/dashboard")
async def dashboard(request: Request):
    user = request.session.get("user")
    if user:
        email = user.get("email", "User")
        return {"message": f"Welcome, {email}!"}
    return RedirectResponse(url=f"{SERVER_ROUTE_PREFIX}/login/google")

@app.get(f"{SERVER_ROUTE_PREFIX}/settings")
async def settings(request: Request):
    user = request.session.get("user")
    if user:
        return {"settings": "Your personal settings"}
    return RedirectResponse(url=f"{SERVER_ROUTE_PREFIX}/login/google")

@app.post("/test-login")
def test_login(request: Request):
    # Simulate a logged-in user in session
    request.session["user"] = {"email": TEST_USERNAME}
    return {"message": "Test login successful"}

# --------- GOOGLE LOGIN ----------
@app.get(f"{SERVER_ROUTE_PREFIX}/login/google")
async def login_google(request: Request):
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")
    print("GOOGLE_CLIENT_ID:", GOOGLE_CLIENT_ID[:6], "...", GOOGLE_CLIENT_ID[-6:] if GOOGLE_CLIENT_ID else "")
    print("Redirect URI (Google):", GOOGLE_REDIRECT_URI)
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

@app.get(f"/auth/google/callback")
async def auth_google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = await oauth.google.userinfo(token=token)
    request.session["user"] = dict(user_info)
    return RedirectResponse(url=f"{SERVER_ROUTE_PREFIX}/")

# --------- COGNITO LOGIN ----------
@app.get(f"{SERVER_ROUTE_PREFIX}/login")
async def login_cognito(request: Request):
    # Debugging session before starting login
    print("Session at /login (before redirect):", request.session)
    return await oauth.oidc.authorize_redirect(request, COGNITO_REDIRECT_URI)

@app.get(f"/auth/callback")
async def auth_cognito_callback(request: Request):
    token = await oauth.oidc.authorize_access_token(request)
    user = await oauth.oidc.userinfo(token=token)
    # user is typically a dict-like object from OIDC userinfo
    request.session["user"] = dict(user)
    user = request.session.get("user")
    if user:
        email = user.get("email") or user.get("preferred_username") or "User"
        sub = user.get("sub")
        email_verified = user.get("email_verified")
        user_name = user.get("username")
    return RedirectResponse(url=f"{SERVER_ROUTE_PREFIX}/")

@app.get(f"{SERVER_ROUTE_PREFIX}/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url=f"/")

# ---------------------------------------------
# Attach your protected routes (kept from your code)
# ---------------------------------------------
try:
    app.include_router(protected_router)
except Exception as e:
    print("[WARN] Could not include protected_router:", e)



# Example URL: https://0.0.0.0:443/e3/?file=email_design1.html
@app.get(f"{SERVER_ROUTE_PREFIX}/", response_class=HTMLResponse)
async def serve_index(request: Request, file: str = Query("editor.html")):
    user = request.session.get("user")
    if user:
        email = user.get("email") or user.get("preferred_username") or "User"
        print(file)
        # Sanitize filename to prevent directory traversal
        if ".." in file or "/" in file or "\\" in file:
            return HTMLResponse(content="❌ Invalid file name", status_code=400)


        js_files = list_directory_sorted(os.path.join(html_path, "js"))
        css_files = list_directory_sorted(os.path.join(html_path, "css"))

        return templates.TemplateResponse("editor.html", {
            "request": request,
            "DESIGN_FILE": file,
            "CLIENT_ROUTE_PREFIX": CLIENT_ROUTE_PREFIX,
            "SERVER_ROUTE_PREFIX": SERVER_ROUTE_PREFIX,
            "js_files": js_files,
            "css_files": css_files
        })
    return RedirectResponse(url="/")

# # ------------------------
# # 📡 AI Agent Endpoint
# # ------------------------

@app.post(f"{SERVER_ROUTE_PREFIX}/ai_agent")
async def ai_agent(request: Request, payload: dict = Body(...)):
    try:
        print(payload.get("message"))
        response = route_ai_request(query=payload.get("message"))
        print({"response": response})
        return {"response": response}
    except Exception as e:
        return {"error": str(e)}


# @app.post(f"{SERVER_ROUTE_PREFIX}/ai_agent")
# async def ai_agent(request: Request, payload: object):
# # async def ai_agent(request: Request, payload: AIRequest):
#     # user = request.session.get("user")
#     # if user:
#     try:
#         print(payload.message)
#         response = route_ai_request(query=payload.message)  # replace with actual logic
#         print({"response": response})
#         return {"response": response}  # or response.choices[0]...
#     except Exception as e:
#         return {"error": str(e)}


# ------------------------
# 📈 View Metrics (Image)
# ------------------------
@app.get(f"{SERVER_ROUTE_PREFIX}/view_metrics")
async def view_metrics():
    try:
        saved_metrics_path = METRICS_DIR + "/email_metrics_current.png"
        get_metrics(saved_metrics_path=saved_metrics_path)
        metrics_path = os.path.abspath(saved_metrics_path)
        if not os.path.exists(metrics_path):
            return JSONResponse(status_code=404, content={"error": "Metrics image not found."})
        return FileResponse(metrics_path, media_type="image/png")
    except Exception as e:
        return {"error": str(e)}



# # ------------------------
# # 💾 Save Email Config
# # ------------------------


@app.post(f"{SERVER_ROUTE_PREFIX}/save_email_config")
async def save_email_config(
    payload: SendEmailConfigPayload,
    file: str = Query("email_design.html")
):
    try:
        print(payload)

        # Basic file name sanitization
        if ".." in file or "/" in file or "\\" in file:
            return {"error": "Invalid file name"}

        # Replace .html with .json if present
        if file.endswith(".html"):
            file = file[:-5] + ".json"

        # Ensure it ends with .json
        if not file.endswith(".json"):
            file += ".json"

        filepath = EMAIL_DESIGN_DIR / file
        payload_dict = payload.dict()

        with open(filepath, "w") as f:
            json.dump(payload_dict, f, indent=2)

        return {"status": "success", "message": f"Config saved to {filepath}"}
    except Exception as e:
        return {"error": str(e)}



# ------------------------
# 📤 Send Email
# ------------------------


@app.post(f"{SERVER_ROUTE_PREFIX}/send_campaign")
async def send_email(payload: SendEmailPayload):
    try:
        print("debug info: /send_campaign called")
        # Define path to the contacts file
        contacts_file = Path(CONTACTS_DIR + "/contacts.tsv")

        # Check if the file exists
        print("debug info: contacts file path")
        print(contacts_file)
        if not contacts_file.exists():
            print("debug info: contacts.tsv file does NOT EXIST!")
            print(f"Contacts file not found: {contacts_file}")
            raise HTTPException(status_code=404, detail=f"❌ No contacts found. Please get contacts.")

        initiate_email_send(design_name=payload.design_name, html_email_design=payload.html_email_design, subject=payload.subject, preview=payload.preview, from_data=payload.from_data, tracking=payload.tracking, send_date=payload.send_date)
        return "OK"

    except HTTPException as he:
        print(dir(he))
        raise he  # Let FastAPI handle HTTP error properly
    except Exception as e:
        print(dir(e))
        return {"error": str(e)}  # Handle unexpected errors gracefully




@app.post(f"{SERVER_ROUTE_PREFIX}/schedule_campaign")
async def send_email(payload: SendEmailPayload):
    try:
        print("debug info: /send_email called")

        # Define path to the contacts file
        contacts_file = Path("backend/storage/contacts/contacts.tsv")

        print("debug info: contacts file path")
        print(contacts_file)
        if not contacts_file.exists():
            raise HTTPException(status_code=404, detail=f"❌ Contacts file not found: {contacts_file}")

        # Load config
        config_path = Path("email_designs/email_design.json")
        with open(config_path, "r") as f:
            config_data = json.load(f)

        print("Loaded config data:")
        print(config_data)

        # Simulate internal POST to /schedule_campaign
        response = client.post(f"{SERVER_ROUTE_PREFIX}/schedule_campaign", json=config_data)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return {
            "status": "campaign scheduled",
            "details": response.json()
        }

    except Exception as e:
        return {"error": str(e)}


# ------------------------
# ⬇️ Download Contacts (TSV)
# ------------------------
@app.get(f"{SERVER_ROUTE_PREFIX}/download_contacts")
async def download_contacts():
    try:
        path = os.path.abspath(f"{CONTACTS_DIR}/contacts.tsv")
        if not os.path.exists(path):
            return JSONResponse(status_code=404, content={"error": "contacts.tsv not found."})
        return FileResponse(path, filename="contacts.tsv", media_type="text/tab-separated-values")
    except Exception as e:
        return {"error": str(e)}


@app.post(f"{SERVER_ROUTE_PREFIX}/upload_contacts")
async def upload_contacts(file: UploadFile = File(...)):

    # remove existing tsv files in CONTACTS_DIR if files exist
    for __file in os.listdir(CONTACTS_DIR):
        if __file.endswith(".tsv"):
            os.remove(os.path.join(CONTACTS_DIR, __file))

    # basic content-type / extension check
    allowed_ct = {
        "text/tab-separated-values", "text/plain", "text/csv",
        "application/vnd.ms-excel", "application/csv",
    }
    print("FILE VAR")
    print(file)
    if (file.content_type not in allowed_ct) and not file.filename.lower().endswith((".tsv", ".csv")):
        raise HTTPException(status_code=415, detail="Please upload a .tsv or .csv file.")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file.")

    text = raw.decode("utf-8", errors="ignore")
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="\t,")
        delim = dialect.delimiter
    except Exception:
        # fallback: prefer TSV if tabs present, else comma
        delim = "\t" if ("\t" in sample) else ","

    try:
        df = pd.read_csv(io.StringIO(text), sep=delim, dtype=str).fillna("")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {e}")

    required = ["id","first_name","last_name","email","phone","company","job_title","city","state","country"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing columns: {', '.join(missing)}")

    # Optional: basic email sanity
    if "email" in df.columns:
        df["email"] = df["email"].str.strip()

    # Save a normalized TSV snapshot
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = CONTACTS_DIR + f"/contacts.tsv"
    df.to_csv(out_path, sep="\t", index=False)



    print("debug info: importing tsv files")
    import_tsv_files(TSV_DIRECTORY=CONTACTS_DIR)
    print("debug info: tsv files imported")

    return JSONResponse({
        "ok": True,
        "rows": int(df.shape[0]),
        "saved": out_path,
        "delimiter": "\\t" if delim == "\t" else ","
    })


# ------------------------
# 💾 Save HTML Email Design
# ------------------------

@app.get(f"{SERVER_ROUTE_PREFIX}/raw_email_designs", response_class=HTMLResponse)
async def get_raw_email_design(file: str = Query(...)):
    # Basic sanitization to prevent directory traversal
    if ".." in file or "/" in file or "\\" in file:
        return HTMLResponse("❌ Invalid file path", status_code=400)

    file_path = os.path.join("email_designs", file)
    if not os.path.isfile(file_path):
        return HTMLResponse("❌ File not found", status_code=404)

    response = FileResponse(path=file_path, media_type="text/html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get(f"{SERVER_ROUTE_PREFIX}/email_designs", response_class=HTMLResponse)
async def view_email_design(file: str = Query(...)):
    # Basic sanitization to prevent directory traversal
    if ".." in file or "/" in file or "\\" in file:
        return HTMLResponse("❌ Invalid file path", status_code=400)

    file_path = os.path.join(EMAIL_DESIGN_DIR, file)
    if not os.path.isfile(file_path):
        return HTMLResponse("❌ File not found", status_code=404)

    response = FileResponse(path=file_path, media_type="text/html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.post(f"{SERVER_ROUTE_PREFIX}/save_email_design")
# async def save_email_design(request: Request, file: str = Query("email_design.html")):
async def save_email_design(file: str = Query("email_design.html"), payload: dict = Body(...)):
    try:
        # payload = await request.json()
        html_content = payload.get("html", "")

        if not html_content:
            return {"error": "Missing 'html' in payload"}

        # Sanitize file name
        if ".." in file or "/" in file or "\\" in file:
            return JSONResponse(content={"error": "Invalid file name"}, status_code=400)

        # Save the HTML content to the specified file
        file_path = os.path.join(EMAIL_DESIGN_DIR, file)
        print(file)
        print(file_path)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # Optional: upload to bucket
        upload_html_design_to_bucket(file_name=file_path)

        return {"status": "success", "message": f"HTML saved to {file_path}"}
    except Exception as e:
        return {"error": str(e)}


def list_directory_sorted(path='.'):
    try:
        items = os.listdir(path)
        sorted_items = sorted(items)
        return sorted_items
    except FileNotFoundError:
        print(f"The directory {path} does not exist.")
        return []
    except PermissionError:
        print(f"Permission denied to access {path}.")
        return []



@app.post(f"{SERVER_ROUTE_PREFIX}/upload_image")
async def upload_image(image: UploadFile = File(...)):
    try:
        filename = f"{image.filename}"
        filepath = os.path.join(IMAGE_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(await image.read())

        upload_html_design_to_bucket(file_name=str(IMAGE_DIR) + "/" + image.filename)

        return {"message": f"Image saved", "url": f"https://e3-designs.s3.amazonaws.com/{image.filename}"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get(f"{SERVER_ROUTE_PREFIX}/list_images")
async def list_images(request: Request):

    files = [
        f"{request.url.scheme }://{request.url.hostname}:{PORT}{SERVER_ROUTE_PREFIX}/images/{f}"
        for f in os.listdir(str(IMAGE_DIR))
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))
    ]
    return files


@app.post(f"{SERVER_ROUTE_PREFIX}/delete_image")
async def delete_image(request: Request):
    try:
        data = await request.json()
        url = data.get("url")
        if not url:
            return JSONResponse(content={"error": "Missing URL"}, status_code=400)

        # Extract file name from URL
        filename = os.path.basename(urlparse(url).path)
        filepath = os.path.join(IMAGE_DIR, filename)

        if os.path.exists(filepath):
            os.remove(filepath)
            return {"status": "success", "message": f"Deleted {filename}"}
        else:
            return JSONResponse(content={"error": "File not found"}, status_code=404)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



# @app.post(f"{SERVER_ROUTE_PREFIX}/schedule_campaign", response_model=CampaignScheduleOut)
# def schedule_email(email: CampaignScheduleIn):
#     email_id = str(uuid4())
#     with engine.connect() as conn:
#         print("Adding campaign to database...")
#         conn.execute(text("""
#             INSERT INTO scheduled_campaigns (id, recipient, subject, body, send_at)
#             VALUES (:id, :recipient, :subject, :body, :send_at)
#         """), {
#             "id": email_id,
#             "recipient": email.from_data,
#             "subject": email.subject,
#             "body": email.html_email_design,
#             "send_at": email.send_date,
#         })
#         conn.commit()
#     return CampaignScheduleOut(id=email_id, **email.dict())


# @app.get(f"{SERVER_ROUTE_PREFIX}/scheduled_campaigns", response_model=List[CampaignScheduleOut])
# def list_scheduled_emails():
#     with engine.connect() as conn:
#         result = conn.execute(text("SELECT * FROM scheduled_campaigns"))
#         emails = [dict(row._mapping) for row in result.fetchall()]
#     return emails


# @app.delete(f"{SERVER_ROUTE_PREFIX}/delete_campaign/{{email_id}}")
# def delete_email(email_id: str):
#     with engine.connect() as conn:
#         result = conn.execute(text("""
#             DELETE FROM scheduled_campaigns WHERE id = :id RETURNING id
#         """), {"id": email_id})
#         conn.commit()
#         row = result.fetchone()
#         if not row:
#             raise HTTPException(status_code=404, detail="Email not found")
#     return {"status": "deleted"}

# ------------------------
# 🏁 Run Server
# ------------------------
# if __name__ == '__main__':
#     print("Cleaning up previous contacts.")
#     directory = CONTACTS_DIR

#     for file in directory.glob("*"):
#         if file.is_file():
#             file.unlink()
            
#     uvicorn.run(
#         "api.__main__:app",
#         host="0.0.0.0",
#         port=443,
#         reload=True,
#         # ssl_certfile="cert.pem",
#         # ssl_keyfile="key.pem"
#     )



# ---------------------------------------------
# Run:
# uvicorn z_auth:app --reload --host localhost --port 443
# ---------------------------------------------

