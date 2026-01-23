from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dhanhq import dhanhq
import os
from zoneinfo import ZoneInfo
from datetime import datetime, time

from engines.intraday_breakout_engine import process_intraday_breakout
from engines.intraday_boost_engine import process_intraday_boost
from stocks_master import FO_STOCKS

IST = ZoneInfo("Asia/Kolkata")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🔒 DAY MEMORY (SUSTAINED)
DAY_BREAKOUT = {}
DAY_BOOST = {}


def get_dhan_client():
    return dhanhq(
        os.getenv("CLIENT_ID"),
        os.getenv("ACCESS_TOKEN")
    )


def within_selection_window(now):
    return time(9, 20) <= now.time() <= time(9, 25)


def try_replace(memory, candidate, key_name):
    """
    Replace weakest stock if candidate is stronger
    """
    if len(memory) < 10:
        memory[candidate["symbol"]] = candidate
        return

    weakest = min(
        memory.values(),
        key=lambda x: abs(x[key_name])
    )

    if abs(candidate[key_name]) > abs(weakest[key_name]):
        del memory[weakest["symbol"]]
        memory[candidate["symbol"]] = candidate


@app.get("/intraday-data")
def intraday_data():

    dhan = get_dhan_client()
    now = datetime.now(IST)

    for symbol, sid in FO_STOCKS.items():
        try:
            quote = dhan.quote_data(securities={"NSE_EQ": [sid]})
            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse:
                continue

            data = nse[str(sid)]

            # ================= BREAKOUT =================
            b1 = process_intraday_breakout(symbol, data)
            if b1:
                if within_selection_window(now):
                    try_replace(DAY_BREAKOUT, b1, "rf_pct")
                else:
                    try_replace(DAY_BREAKOUT, b1, "rf_pct")

            # ================= BOOST ====================
            b2 = process_intraday_boost(symbol, data)
            if b2:
                if within_selection_window(now):
                    try_replace(DAY_BOOST, b2, "r_factor")
                else:
                    try_replace(DAY_BOOST, b2, "r_factor")

        except:
            continue

    BREAKOUT_TOP = sorted(
        DAY_BREAKOUT.values(),
        key=lambda x: abs(x["rf_pct"]),
        reverse=True
    )

    BOOST_TOP = sorted(
        DAY_BOOST.values(),
        key=lambda x: abs(x["r_factor"]),
        reverse=True
    )

    return {
        "breakout": BREAKOUT_TOP,
        "boost": BOOST_TOP,
        "time": now.strftime("%I:%M:%S %p")
    }


@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "fo_dashboard.html",
        {"request": request}
    )
