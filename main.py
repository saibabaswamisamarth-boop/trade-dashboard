from datetime import datetime, date

DAY_STATE = {
    "date": date.today().isoformat(),
    "live_memory": {},      # intraday persistence
    "final_snapshot": [],   # market close top 10
    "snapshot_saved": False
}
def is_market_closed():
    return datetime.now().strftime("%H:%M") > "15:30"
from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dhanhq import dhanhq
import os
from engines.intraday_boost_engine import process_intraday_boost

from engines.market_pulse_engine import process_stock
from engines.intraday_boost_engine import process_intraday_boost
from stocks_master import FO_STOCKS

print("Total stocks loaded:", len(FO_STOCKS))

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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
# MARKET PULSE V2 API
# =========================

@app.get("/market-pulse-v2")
def market_pulse_v2(batch: int = Query(1, ge=1)):

    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    total_batches = len(batches)

    if batch > total_batches:
        return {"batch": batch, "total_batches": total_batches, "data": []}

    current_batch = batches[batch - 1]

    for symbol, sid in current_batch:
        try:
            quote = dhan.quote_data(
                securities={"NSE_EQ": [sid]}
            )

            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse:
                continue

            data = nse[str(sid)]

            # 🔥 CORE ENGINE
            result = process_stock(symbol, data)
            results.append(result)

        except Exception as e:
            print(symbol, e)

    # 🔥 TOP STOCK SELECTION (INSIDE FUNCTION)
    results = sorted(
        results,
        key=lambda x: (
            x.get("pulse_score", 0),
            x.get("r_factor", 0),
            x.get("volume", 0)
        ),
        reverse=True
    )

    # 👉 फक्त TOP 10
    results = results[:10]

    return {
        "batch": batch,
        "total_batches": total_batches,
        "data": results
    }




# =========================
# DASHBOARD (HTML)
# =========================

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    @app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )


@app.get("/intraday-boost")
def intraday_boost(batch: int = Query(1, ge=1)):

    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    total_batches = len(batches)

    if batch > total_batches:
        return {
            "batch": batch,
            "total_batches": total_batches,
            "data": []
        }

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
                final_score = update_day_memory(
                    symbol=result["symbol"],
                    score=result["boost_score"]
                )
                result["boost_score"] = final_score
                results.append(result)

        except Exception as e:
            print(symbol, e)

    # 🔥 SORT
    results = sorted(
        results,
        key=lambda x: x["boost_score"],
        reverse=True
    )

    # =========================
    # MARKET CLOSE SNAPSHOT
    # =========================
    if is_market_closed() and not DAY_STATE["snapshot_saved"]:
        DAY_STATE["final_snapshot"] = [
            {"symbol": k, "score": v["score"]}
            for k, v in sorted(
                DAY_STATE["live_memory"].items(),
                key=lambda x: x[1]["score"],
                reverse=True
            )[:10]
        ]
        DAY_STATE["snapshot_saved"] = True

    # =========================
    # FINAL RETURN
    # =========================
    if is_market_closed():
        data = DAY_STATE["final_snapshot"]
    else:
        data = results[:10]

    return {
        "batch": batch,
        "total_batches": total_batches,
        "data": data
    }
@app.get("/api/market-heat")
def market_heat(batch: int = Query(1, ge=1)):
    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    current_batch = batches[batch - 1]

    for symbol, sid in current_batch:
        try:
            quote = dhan.quote_data(securities={"NSE_EQ": [sid]})
            data = quote["data"]["data"]["NSE_EQ"].get(str(sid))
            if not data:
                continue

            r_factor = round(data.get("volume", 0) / 1_000_000, 2)
            pct = ((data["last_price"] - data["ohlc"]["open"]) / data["ohlc"]["open"]) * 100

            results.append({
                "symbol": symbol,
                "pct": round(pct, 2),
                "r_factor": r_factor,
                "signal": "UP" if pct > 0 else "DOWN"
            })
        except:
            pass

    # 🔥 SCANNER SORT
    results = sorted(
        results,
        key=lambda x: (abs(x["pct"]), x["r_factor"]),
        reverse=True
    )[:10]

    return {"data": results}

