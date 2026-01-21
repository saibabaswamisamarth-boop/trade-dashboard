from datetime import datetime, date
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dhanhq import dhanhq
import os

from stocks_master import FO_STOCKS
from engines.market_pulse_engine import process_stock
from engines.intraday_boost_engine import process_intraday_boost

# =========================
# APP SETUP
# =========================

app = FastAPI()
templates = Jinja2Templates(directory="templates")

print("Total F&O stocks loaded:", len(FO_STOCKS))

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
    return [items[i:i+BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]

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

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )

# =========================
# MARKET HEAT API (LEFT PANEL)
# =========================

@app.get("/api/market-heat")
def market_heat(batch: int = Query(1, ge=1)):
    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    current_batch = batches[batch - 1]

    for symbol, sid in current_batch:
        try:
            q = dhan.quote_data(securities={"NSE_EQ": [sid]})
            data = q["data"]["data"]["NSE_EQ"].get(str(sid))
            if not data:
                continue

            open_p = data["ohlc"]["open"]
            last_p = data["last_price"]
            pct = round(((last_p - open_p) / open_p) * 100, 2)
            r_factor = round(data["volume"] / 1_000_000, 2)

            results.append({
                "symbol": symbol,
                "pct": pct,
                "r_factor": r_factor,
                "signal": "UP" if pct > 0 else "DOWN"
            })

        except Exception:
            pass

    results = sorted(
        results,
        key=lambda x: (abs(x["pct"]), x["r_factor"]),
        reverse=True
    )[:10]

    return {"data": results}

# =========================
# INTRADAY BOOST API (RIGHT PANEL)
# =========================

@app.get("/intraday-boost")
def intraday_boost(batch: int = Query(1, ge=1)):
    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    total_batches = len(batches)
    current_batch = batches[batch - 1]

    index_move_pct = 0  # future: NIFTY %

    for symbol, sid in current_batch:
        try:
            q = dhan.quote_data(securities={"NSE_EQ": [sid]})
            data = q["data"]["data"]["NSE_EQ"].get(str(sid))
            if not data:
                continue

            r = process_intraday_boost(symbol, data, index_move_pct)
            if not r:
                continue

            r["boost_score"] = update_day_memory(
                r["symbol"],
                r["boost_score"]
            )
            results.append(r)

        except Exception as e:
            print(symbol, e)

    results = sorted(
        results,
        key=lambda x: x["boost_score"],
        reverse=True
    )

    # Market close snapshot
    if is_market_closed() and not DAY_STATE["snapshot_saved"]:
        DAY_STATE["final_snapshot"] = results[:10]
        DAY_STATE["snapshot_saved"] = True

    data = DAY_STATE["final_snapshot"] if is_market_closed() else results[:10]

    return {
        "batch": batch,
        "total_batches": total_batches,
        "data": data
    }
