from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dhanhq import dhanhq
import os
from datetime import datetime, date

from engines.intraday_boost_engine import process_intraday_boost
from stocks_master import FO_STOCKS

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# -----------------------------
# DAY MEMORY (SUSTAIN LOGIC)
# -----------------------------
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

    # sustain bonus
    if mem["hits"] >= 2:
        score += 2
    if score > mem["score"]:
        score += 2
    if (now - mem["first_seen"]).seconds > 1800:
        score += 3

    mem["score"] = score
    return score


# -----------------------------
# STOCK BATCHING
# -----------------------------
FO_STOCKS_FULL = FO_STOCKS
BATCH_SIZE = 200

def get_batches(stock_dict):
    items = list(stock_dict.items())
    return [items[i:i+BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]


# -----------------------------
# DHAN CLIENT
# -----------------------------
def get_dhan_client():
    client_id = os.getenv("CLIENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")
    if not client_id or not access_token:
        raise Exception("Dhan ENV variables not set")
    return dhanhq(client_id, access_token)


# -----------------------------
# ROUTES
# -----------------------------
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/intraday-boost")
def intraday_boost(batch: int = Query(1, ge=1)):

    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    total_batches = len(batches)

    if batch > total_batches:
        return {"batch": batch, "total_batches": total_batches, "data": []}

    current_batch = batches[batch - 1]

    for symbol, sid in current_batch:
        try:
            quote = dhan.quote_data(securities={"NSE_EQ": [sid]})
            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse:
                continue

            data = nse[str(sid)]

            # 🔥 R-FACTOR ENGINE CALL
            result = process_intraday_boost(symbol, data)

            if result:
                final_score = update_day_memory(
                    result["symbol"],
                    result["boost_score"]
                )
                result["boost_score"] = final_score
                results.append(result)

        except Exception as e:
            print(symbol, e)

    # 🔥 SORTING BY R-FACTOR / BOOST SCORE
    results = sorted(results, key=lambda x: x["boost_score"], reverse=True)

    # 🔒 Market close snapshot
    if is_market_closed() and not DAY_STATE["snapshot_saved"]:
        DAY_STATE["final_snapshot"] = results[:10]
        DAY_STATE["snapshot_saved"] = True

    data = DAY_STATE["final_snapshot"] if is_market_closed() else results[:10]

    return {
        "batch": batch,
        "total_batches": total_batches,
        "data": data
    }


@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )
