from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dhanhq import dhanhq
import os
from datetime import datetime, date

from engines.intraday_boost_engine import process_intraday_boost
from engines.market_pulse_engine import process_stock
from stocks_master import FO_STOCKS

# =========================
# APP SETUP
# =========================

app = FastAPI()
templates = Jinja2Templates(directory="templates")

print("Total stocks loaded:", len(FO_STOCKS))

# =========================
# DAY MEMORY (LEVEL 3 LOGIC)
# =========================

DAY_STATE = {
    "date": date.today().isoformat(),
    "live_memory": {},
    "final_snapshot": [],
    "snapshot_saved": False
}

def is_market_closed():
    return datetime.now().strftime("%H:%M") > "15:30"

def update_day_memory(symbol, score):
    now = datetime.now()
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
    if (now - mem["first_seen"]).seconds > 1800:
        score += 3

    mem["score"] = score
    return score

# =========================
# GLOBAL DATA
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
# INTRADAY BOOST API
# =========================

@app.get("/intraday-boost")
def intraday_boost(batch: int = Query(1, ge=1)):

    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    total_batches = len(batches)
    if batch > total_batches:
        return {"batch": batch, "total_batches": total_batches, "data": []}

    current_batch = batches[batch - 1]
    index_move_pct = 0

    for symbol, sid in current_batch:
        try:
            quote = dhan.quote_data(securities={"NSE_EQ": [sid]})
            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse:
                continue

            data = nse[str(sid)]
            result = process_intraday_boost(symbol, data, index_move_pct)

            if result:
                result["boost_score"] = update_day_memory(
                    result["symbol"],
                    result["boost_score"]
                )
                results.append(result)

        except Exception as e:
            print(symbol, e)

    results = sorted(results, key=lambda x: x["boost_score"], reverse=True)

    if is_market_closed():
        if not DAY_STATE["snapshot_saved"]:
            DAY_STATE["final_snapshot"] = results[:10]
            DAY_STATE["snapshot_saved"] = True
        data = DAY_STATE["final_snapshot"]
    else:
        data = results[:10]

    return {
        "batch": batch,
        "total_batches": total_batches,
        "data": data
    }

# =========================
# DASHBOARD ROUTE
# =========================

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )
