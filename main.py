from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dhanhq import dhanhq
import os

from engines.market_pulse_engine import process_stock
from engines.intraday_boost_engine import process_intraday_boost
from stocks_master import FO_STOCKS

app = FastAPI()
templates = Jinja2Templates(directory="templates")

FO_STOCKS_FULL = FO_STOCKS
BATCH_SIZE = 200

def get_batches(stock_dict):
    items = list(stock_dict.items())
    return [items[i:i+BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]

def get_dhan_client():
    return dhanhq(
        os.getenv("CLIENT_ID"),
        os.getenv("ACCESS_TOKEN")
    )

@app.get("/health")
def health():
    return {"status": "ok"}

# =========================
# MARKET PULSE (RAW – ALL STOCKS)
# =========================
@app.get("/market-pulse-v2")
def market_pulse_v2(batch: int = Query(1, ge=1)):
    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    total_batches = len(batches)

    if batch > total_batches:
        return {"batch": batch, "total_batches": total_batches, "data": []}

    for symbol, sid in batches[batch - 1]:
        try:
            q = dhan.quote_data(securities={"NSE_EQ": [sid]})
            data = q.get("data", {}).get("data", {}).get("NSE_EQ", {}).get(str(sid))
            if not data:
                continue

            results.append(process_stock(symbol, data))
        except:
            pass

    return {
        "batch": batch,
        "total_batches": total_batches,
        "data": results
    }

# =========================
# INTRADAY BOOST (TOP STOCKS)
# =========================
@app.get("/intraday-boost")
def intraday_boost(batch: int = Query(1, ge=1)):
    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    total_batches = len(batches)

    if batch > total_batches:
        return {"batch": batch, "total_batches": total_batches, "data": []}

    for symbol, sid in batches[batch - 1]:
        try:
            q = dhan.quote_data(securities={"NSE_EQ": [sid]})
            data = q.get("data", {}).get("data", {}).get("NSE_EQ", {}).get(str(sid))
            if not data:
                continue

            results.append(
                process_intraday_boost(symbol, data, index_move_pct=0)
            )
        except:
            pass

    results = sorted(
        results,
        key=lambda x: (x["boost_score"], x["r_factor"]),
        reverse=True
    )

    return {
        "batch": batch,
        "total_batches": total_batches,
        "data": results[:20]   # TOP 20 (change as needed)
    }

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "fo_dashboard.html",
        {"request": request}
    )
