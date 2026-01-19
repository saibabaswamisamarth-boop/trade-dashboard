import os
import time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dhanhq import dhanhq

app = FastAPI()

# -------------------------
# SAFE DHAN CLIENT
# -------------------------
def get_dhan_client():
    client_id = os.getenv("CLIENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")

    if not client_id or not access_token:
        raise Exception("Dhan ENV variables not set")

    return dhanhq(client_id, access_token)

# -------------------------
# HEALTH CHECK
# -------------------------
@app.get("/health")
def health():
    return {
        "CLIENT_ID": bool(os.getenv("CLIENT_ID")),
        "ACCESS_TOKEN": bool(os.getenv("ACCESS_TOKEN"))
    }

# -------------------------
# DUMMY ROUTES (TEMP)
# -------------------------
@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/pro-dashboard", response_class=HTMLResponse)
def pro_dashboard():
    return HTMLResponse("""
    <html>
      <body style="background:#0b1220;color:white;text-align:center;">
        <h1>🔥 Trade Dashboard LIVE</h1>
        <p>If you see this, deployment is SUCCESS ✅</p>
      </body>
    </html>
    """)
