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

# ---------------- DAY MEMORY ----------------
DAY_STATE = {
    "date": date.today().isoformat(),
    "breakout": {},
    "boost": {}
}

def reset_day():
    today = date.today().isoformat()
    if DAY_STATE["date"] != today:
        DAY_STATE["date"] = today
        DAY_STATE["breakout"] = {}
        DAY_STATE["boost"] = {}

# ---------------- DHAN ----------------
def get_dhan_client():
    return dhanhq(
        os.getenv("CLIENT_ID"),
        os.getenv("ACCESS_TOKEN")
    )

# ---------------- MAIN API ----------------
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

            # -------- BREAKOUT --------
            b1 = process_intraday_breakout(symbol, data)
            if b1:
                if symbol not in DAY_STATE["breakout"]:
                    if len(DAY_STATE["breakout"]) < 10:
                        DAY_STATE["breakout"][symbol] = b1
                else:
                    DAY_STATE["breakout"][symbol].update(b1)

            # -------- BOOST --------
            b2 = process_intraday_boost(symbol, data)
            if b2:
                if symbol not in DAY_STATE["boost"]:
                    if len(DAY_STATE["boost"]) < 10:
                        DAY_STATE["boost"][symbol] = b2
                else:
                    DAY_STATE["boost"][symbol].update(b2)

        except:
            continue

    breakout_list = sorted(
        DAY_STATE["breakout"].values(),
        key=lambda x: x["move_pct"],
        reverse=True
    )

    boost_list = sorted(
        DAY_STATE["boost"].values(),
        key=lambda x: x["r_factor"],
        reverse=True
    )

    return {
        "breakout": breakout_list,
        "boost": boost_list,
        "time": datetime.now(IST).strftime("%I:%M:%S %p")
    }

# ---------------- DASHBOARD ----------------
@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "fo_dashboard.html",
        {"request": request}
    )
