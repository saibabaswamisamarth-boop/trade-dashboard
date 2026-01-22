from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dhanhq import dhanhq
import os
import json
from datetime import datetime, date
from zoneinfo import ZoneInfo

from engines.intraday_boost_engine import (
    process_intraday_boost,
    process_intraday_breakout
)
from stocks_master import FO_STOCKS

# =========================
# TIMEZONE (IST)
# =========================

IST = ZoneInfo("Asia/Kolkata")

def now_ist():
    return datetime.now(IST)

def now_hm():
    return now_ist().strftime("%H:%M")

def now_str():
    return now_ist().strftime("%H:%M:%S")

# =========================
# APP
# =========================

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# =========================
# SNAPSHOT (POST MARKET)
# =========================

SNAPSHOT_FILE = "last_snapshot.json"

def save_snapshot(data):
    try:
        with open(SNAPSHOT_FILE, "w") as f:
            json.dump(data, f)
    except:
        pass

def load_snapshot():
    try:
        with open(SNAPSHOT_FILE, "r") as f:
            return json.load(f)
    except:
        return []

# =========================
# DAY MEMORY (BOOST)
# =========================

DAY_STATE = {
    "date": date.today().isoformat(),
    "live_memory": {},
    "final_snapshot": [],
    "snapshot_saved": False
}

def is_market_closed():
    return now_hm() >= "15:30"

def update_day_memory(symbol, score):
    mem = DAY_STATE["live_memory"].get(symbol)

    if not mem:
        DAY_STATE["live_memory"][symbol] = {
            "hits": 1,
            "score": score
        }
        return score

    mem["hits"] += 1
    if score > mem["score"]:
        score += 2

    mem["score"] = score
    return score

# =========================
# DHAN CLIENT
# =========================

def get_dhan():
    cid = os.getenv("CLIENT_ID")
    token = os.getenv("ACCESS_TOKEN")
    if not cid or not token:
        raise Exception("Dhan ENV missing")
    return dhanhq(cid, token)

# =========================
# ROUTES
# =========================

@app.get("/health")
def health():
    return {"status": "ok"}

# =========================
# INTRADAY API
# =========================

@app.get("/intraday-boost")
def intraday_boost(batch: int = Query(1, ge=1)):

    if now_hm() < "09:15":
        return {
            "generated_at": now_str(),
            "data": {
                "candidates": [],
                "boosted": load_snapshot()
            }
        }

    dhan = get_dhan()
    candidates = []
    boosted = []

    for symbol, sid in FO_STOCKS.items():
        try:
            quote = dhan.quote_data(securities={"NSE_EQ": [sid]})

            nse = (
                quote.get("data", {})
                     .get("data", {})
                     .get("NSE_EQ", {})
            )

            if str(sid) not in nse:
                continue

            data = nse[str(sid)]

            # LEFT PANEL – BREAKOUT
            br = process_intraday_breakout(symbol, data)
            if br:
                candidates.append(br)

            # RIGHT PANEL – BOOST
            bs = process_intraday_boost(symbol, data)
            if bs:
                bs["boost_score"] = update_day_memory(
                    bs["symbol"], bs["boost_score"]
                )
                boosted.append(bs)

        except Exception as e:
            print("ERROR:", symbol, e)

    candidates = sorted(
        candidates,
        key=lambda x: (x.get("boost_score", 0), x.get("move_pct", 0)),
        reverse=True
    )[:10]

    boosted = sorted(
        boosted,
        key=lambda x: x["boost_score"],
        reverse=True
    )[:10]

    if is_market_closed():
        if not DAY_STATE["snapshot_saved"]:
            DAY_STATE["final_snapshot"] = boosted
            save_snapshot(boosted)
            DAY_STATE["snapshot_saved"] = True
        boosted = DAY_STATE["final_snapshot"]
        candidates = []

    return {
        "generated_at": now_str(),
        "data": {
            "candidates": candidates,
            "boosted": boosted
        }
    }

# =========================
# DASHBOARD
# =========================

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )
