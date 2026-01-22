from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dhanhq import dhanhq
import os
from zoneinfo import ZoneInfo
from datetime import datetime, date

from engines.intraday_breakout_engine import process_intraday_breakout
from engines.intraday_boost_engine import process_intraday_boost
from stocks_master import FO_STOCKS

IST = ZoneInfo("Asia/Kolkata")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DAY_DATE = date.today().isoformat()
DAY_BREAKOUT_MEMORY = {}
DAY_BOOST_MEMORY = {}


def reset_day():
    global DAY_DATE, DAY_BREAKOUT_MEMORY, DAY_BOOST_MEMORY
    today = date.today().isoformat()
    if DAY_DATE != today:
        DAY_DATE = today
        DAY_BREAKOUT_MEMORY = {}
        DAY_BOOST_MEMORY = {}


def get_dhan_client():
    return dhanhq(
        os.getenv("CLIENT_ID"),
        os.getenv("ACCESS_TOKEN")
    )


@app.get("/intraday-data")
def intraday_data():

    reset_day()
    dhan = get_dhan_client()

    for symbol, sid in FO_STOCKS.items():
        try:
            quote = dhan.quote_data(securities={"NSE_EQ": [sid]})
            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse:
                continue

            data = nse[str(sid)]

            # -------- BREAKOUT PURE LOCK --------
            b1 = process_intraday_breakout(symbol, data)
            if b1:
                if symbol in DAY_BREAKOUT_MEMORY:
                    DAY_BREAKOUT_MEMORY[symbol].update(b1)
                elif len(DAY_BREAKOUT_MEMORY) < 10:
                    DAY_BREAKOUT_MEMORY[symbol] = b1

            # -------- BOOST PURE LOCK --------
            b2 = process_intraday_boost(symbol, data)
            if b2:
                if symbol in DAY_BOOST_MEMORY:
                    DAY_BOOST_MEMORY[symbol].update(b2)
                elif len(DAY_BOOST_MEMORY) < 10:
                    DAY_BOOST_MEMORY[symbol] = b2

        except:
            continue

    return {
        "breakout": list(DAY_BREAKOUT_MEMORY.values()),
        "boost": list(DAY_BOOST_MEMORY.values()),
        "time": datetime.now(IST).strftime("%I:%M:%S %p")
    }


@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "fo_dashboard.html",
        {"request": request}
    )
