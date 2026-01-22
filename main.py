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


def get_dhan_client():
    return dhanhq(
        os.getenv("CLIENT_ID"),
        os.getenv("ACCESS_TOKEN")
    )


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

            b1 = process_intraday_breakout(symbol, data)
            if b1:
                breakout_list.append(b1)

            b2 = process_intraday_boost(symbol, data)
            if b2:
                boost_list.append(b2)

        except:
            continue

    breakout_list = sorted(
        breakout_list,
        key=lambda x: x["move_pct"],
        reverse=True
    )[:10]

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


@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "fo_dashboard.html",
        {"request": request}
    )
