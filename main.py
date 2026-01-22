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

# -------- SMART DAY MEMORY --------
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

# -------- DHAN --------
def get_dhan_client():
    return dhanhq(
        os.getenv("CLIENT_ID"),
        os.getenv("ACCESS_TOKEN")
    )

# -------- MAIN API --------
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

            # -------- BREAKOUT SMART LOCK --------
            b1 = process_intraday_breakout(symbol, data)
            if b1:
                rf = b1["rf_pct"]

                if symbol in DAY_BREAKOUT_MEMORY:
                    DAY_BREAKOUT_MEMORY[symbol] = b1

                elif len(DAY_BREAKOUT_MEMORY) < 10:
                    DAY_BREAKOUT_MEMORY[symbol] = b1

                else:
                    weakest = min(
                        DAY_BREAKOUT_MEMORY.items(),
                        key=lambda x: x[1]["rf_pct"]
                    )
                    if rf > weakest[1]["rf_pct"]:
                        del DAY_BREAKOUT_MEMORY[weakest[0]]
                        DAY_BREAKOUT_MEMORY[symbol] = b1

            # -------- BOOST SMART LOCK --------
            b2 = process_intraday_boost(symbol, data)
            if b2:
                rf = b2["r_factor"]

                if symbol in DAY_BOOST_MEMORY:
                    DAY_BOOST_MEMORY[symbol] = b2

                elif len(DAY_BOOST_MEMORY) < 10:
                    DAY_BOOST_MEMORY[symbol] = b2

                else:
                    weakest = min(
                        DAY_BOOST_MEMORY.items(),
                        key=lambda x: x[1]["r_factor"]
                    )
                    if rf > weakest[1]["r_factor"]:
                        del DAY_BOOST_MEMORY[weakest[0]]
                        DAY_BOOST_MEMORY[symbol] = b2

        except:
            continue

    breakout_list = sorted(
        DAY_BREAKOUT_MEMORY.values(),
        key=lambda x: x["rf_pct"],
        reverse=True
    )

    boost_list = sorted(
        DAY_BOOST_MEMORY.values(),
        key=lambda x: x["r_factor"],
        reverse=True
    )

    return {
        "breakout": breakout_list,
        "boost": boost_list,
        "time": datetime.now(IST).strftime("%I:%M:%S %p")
    }

# -------- DASHBOARD --------
@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "fo_dashboard.html",
        {"request": request}
    )
