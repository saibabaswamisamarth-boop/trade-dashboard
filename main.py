from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dhanhq import dhanhq
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from engines.intraday_boost_engine import process_intraday_breakout
from stocks_master import FO_STOCKS

IST = ZoneInfo("Asia/Kolkata")

def now_str():
    return datetime.now(IST).strftime("%H:%M:%S")

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def get_dhan():
    return dhanhq(
        os.getenv("CLIENT_ID"),
        os.getenv("ACCESS_TOKEN")
    )

@app.get("/intraday-boost")
def intraday_boost():

    dhan = get_dhan()
    results = []

    for symbol, sid in FO_STOCKS.items():
        try:
            quote = dhan.quote_data(securities={"NSE_EQ": [sid]})
            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse:
                continue

            data = nse[str(sid)]
            br = process_intraday_breakout(symbol, data)

            if br:
                results.append(br)

        except Exception as e:
            print(symbol, e)

    # 🔥 FINAL RANKING
    results = sorted(
        results,
        key=lambda x: (
            x["boost_score"],
            x["move_pct"]
        ),
        reverse=True
    )

    # ✅ Always top 10
    top10 = results[:10]

    return {
        "generated_at": now_str(),
        "data": {
            "candidates": top10,
            "boosted": []
        }
    }

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request}
    )
