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

def now_ist_hm():
    return now_ist().strftime("%H:%M")

def now_ist_str():
    return now_ist().strftime("%H:%M:%S")

# =========================
# APP SETUP
# =========================

app = FastAPI()
templates = Jinja2Templates(directory="templates")

print("Total F&O stocks loaded:", len(FO_STOCKS))

# =========================
# SNAPSHOT FILE
# =========================

SNAPSHOT_FILE = "last_snapshot.json"

def save_snapshot_to_file(data):
    try:
        with open(SNAPSHOT_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print("Snapshot save error:", e)

def load_snapshot_from_file():
    try:
        with open(SNAPSHOT_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

# =========================
# DAY MEMORY
# =========================

DAY_STATE = {
    "date": date.today().isoformat(),
    "live_memory": {},
    "final_snapshot": [],
    "snapshot_saved": False
}

def is_market_closed():
    return now_ist_hm() >= "15:30"

def is_early_market():
    return "09:15" <= now_ist_hm() <= "09:35"

def update_day_memory(symbol, score):
    now = now_ist()
    mem = DAY_STATE["live_memory"].get(symbol)

    if not mem:
        DAY_STATE["live_memory"][symbol] = {
            "hits": 1,
            "first_seen": now,
            "last_seen": now,
            "score": score
        }
        return score

    mem["hits"] += 1
    mem["last_seen"] = now

    if mem["hits"] >= 2:
        score += 2
    if score > mem["score"]:
        score += 2
    if (now - mem["first_seen"]).seconds >= 1800:
        score += 3

    mem["score"] = score
    return score

# =========================
# CACHE
# =========================

LAST_ENGINE_RUN = None
CACHED_RESPONSE = None
ENGINE_INTERVAL_SEC = 120

def should_run_engine():
    global LAST_ENGINE_RUN
    now = now_ist()

    if LAST_ENGINE_RUN is None:
        LAST_ENGINE_RUN = now
        return True

    if (now - LAST_ENGINE_RUN).seconds >= ENGINE_INTERVAL_SEC:
        LAST_ENGINE_RUN = now
        return True

    return False

# =========================
# SIGNAL LABEL
# =========================

def elite_signal(score):
    if score >= 18:
        return "ELITE 🚀"
    elif score >= 14:
        return "STRONG 🔥"
    elif score >= 10:
        return "BUILDING ⚡"
    else:
        return "WATCH 👀"

# =========================
# STOCK BATCHING
# =========================

FO_STOCKS_FULL = FO_STOCKS
BATCH_SIZE = 200

def get_batches(stock_dict):
    items = list(stock_dict.items())
    return [items[i:i + BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]

# =========================
# DHAN CLIENT
# =========================

def get_dhan_client():
    client_id = os.getenv("CLIENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")
    if not client_id or not access_token:
        raise Exception("Dhan ENV variables not set")
    return dhanhq(client_id, access_token)

# =========================
# BASIC ROUTES
# =========================

@app.get("/health")
def health():
    return {"status": "ok"}

# =========================
# INTRADAY ENGINE API
# =========================

@app.get("/intraday-boost")
def intraday_boost(batch: int = Query(1, ge=1)):
    global CACHED_RESPONSE

    now_hm = now_ist_hm()

    # -------- PRE-MARKET --------
    if now_hm < "09:15":
        return {
            "generated_at": now_ist_str(),
            "market_status": "CLOSED",
            "data": {
                "candidates": [],
                "boosted": load_snapshot_from_file()
            }
        }

    # -------- CACHE --------
    if not is_early_market():
        if not should_run_engine() and CACHED_RESPONSE:
            return CACHED_RESPONSE

    dhan = get_dhan_client()
    candidates = []
    boosted = []

    batches = get_batches(FO_STOCKS_FULL)
    if batch > len(batches):
        return {"data": {"candidates": [], "boosted": []}}

    current_batch = batches[batch - 1]
    index_move_pct = 0

    for symbol, sid in current_batch:
        try:
            quote = dhan.quote_data(securities={"NSE_EQ": [sid]})

            # ✅ FINAL CORRECT DATA PATH
            nse = (
                quote
                .get("data", {})
                .get("data", {})
                .get("NSE_EQ", {})
            )

            if str(sid) not in nse:
                continue

            data = nse[str(sid)]

            # LEFT PANEL
            breakout = process_intraday_breakout(symbol, data, index_move_pct)
            if breakout:
                candidates.append(breakout)

            # RIGHT PANEL
            boost = process_intraday_boost(symbol, data, index_move_pct)
            if boost:
                final_score = update_day_memory(
                    boost["symbol"],
                    boost["boost_score"]
                )
                boost["boost_score"] = final_score
                boost["signal"] = elite_signal(final_score)
                boosted.append(boost)

        except Exception as e:
            print("ERROR:", symbol, e)

    candidates = sorted(
        candidates, key=lambda x: x["boost_score"], reverse=True
    )[:10]

    boosted = sorted(
        boosted, key=lambda x: x["boost_score"], reverse=True
    )[:10]

    # -------- MARKET CLOSE --------
    if is_market_closed():
        if not DAY_STATE["snapshot_saved"]:
            DAY_STATE["final_snapshot"] = boosted
            save_snapshot_to_file(boosted)
            DAY_STATE["snapshot_saved"] = True

        boosted = DAY_STATE["final_snapshot"]
        candidates = []

    CACHED_RESPONSE = {
        "generated_at": now_ist_str(),
        "market_status": "LIVE",
        "data": {
            "candidates": candidates,
            "boosted": boosted
        }
    }

    return CACHED_RESPONSE

# =========================
# DASHBOARD UI
# =========================

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )
