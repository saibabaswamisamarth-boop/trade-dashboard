from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dhanhq import dhanhq
import os
from zoneinfo import ZoneInfo
from datetime import datetime

from engines.intraday_breakout_engine import process_intraday_breakout
from engines.intraday_boost_engine import process_intraday_boost
from stocks_master import FO_STOCKS

IST = ZoneInfo("Asia/Kolkata")

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------
# DHAN CLIENT
# ---------------------------------------------
def get_dhan_client():
    return dhanhq(
        os.getenv("CLIENT_ID"),
        os.getenv("ACCESS_TOKEN")
    )


# ---------------------------------------------
# INTRADAY DATA API (FOR DASHBOARD)
# ---------------------------------------------
@app.get("/intraday-data")
def intraday_data():

    dhan = get_dhan_client()

    breakout_list = []
    boost_list = []

    for symbol, sid in FO_STOCKS.items():
        try:
            quote = dhan.quote_data(securities={"NSE_EQ": [sid]})
            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})

            if str(sid) not in nse:
                continue

            data = nse[str(sid)]

            # ------------------ BREAKOUT ------------------
            b1 = process_intraday_breakout(symbol, data)
            if b1:
                breakout_list.append(b1)

            # ------------------ BOOST ------------------
            b2 = process_intraday_boost(symbol, data)
            if b2:
                boost_list.append(b2)

        except Exception as e:
            continue

    # ---------------------------------------------
    # SORTING LOGIC (VERY IMPORTANT)
    # ---------------------------------------------

    # Breakout → movement % नुसार
    breakout_list = sorted(
        breakout_list,
        key=lambda x: x["move_pct"],
        reverse=True
    )[:10]

    # Boost → R Factor नुसार
    boost_list = sorted(
        boost_list,
        key=lambda x: x["r_factor"],
        reverse=True
    )[:10]

    return {
        "breakout": breakout_list,
        "boost": boost_list,
        "time": datetime.now(IST).strftime("%I:%M:%S %p")
    }


# ---------------------------------------------
# DASHBOARD UI
# ---------------------------------------------
@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "fo_dashboard.html",
        {"request": request}
    )
