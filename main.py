from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi import Request
from datetime import datetime
import random

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# ---------------------------------------------------
# DUMMY ENGINE (replace later with your real logic)
# ---------------------------------------------------

def sample_breakout():
    stocks = [
        ("OBEROIRLTY", 7, "BEARISH 2.64%"),
        ("CROMPTON", 7, "BEARISH 2.59%"),
        ("MUTHOOTFIN", 7, "BEARISH 2.58%"),
        ("JINDALSTEL", 7, "BULLISH 2.43%"),
        ("DLF", 7, "BEARISH 2.13%"),
        ("TATACHEM", 7, "BULLISH 2.08%"),
        ("TITAN", 7, "BEARISH 2.06%"),
        ("RECLTD", 6, "BULLISH 1.80%"),
        ("HINDALCO", 6, "BEARISH 1.65%"),
        ("AXISBANK", 6, "BULLISH 1.40%"),
    ]

    return [
        {
            "symbol": s,
            "score": sc,
            "signal": sig
        } for s, sc, sig in stocks
    ]


def sample_boost():
    stocks = [
        ("RELIANCE", 14, 2.4, "BULLISH"),
        ("TCS", 13, 1.8, "BULLISH"),
        ("SBIN", 12, 3.1, "BEARISH"),
        ("INFY", 11, 1.2, "BULLISH"),
        ("ITC", 10, 0.9, "BEARISH"),
    ]

    return [
        {
            "symbol": s,
            "boost": b,
            "r": r,
            "signal": sig
        } for s, b, r, sig in stocks
    ]


# ---------------------------------------------------
# ROUTES
# ---------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/intraday-data")
def intraday_data():
    return {
        "breakout": sample_breakout(),
        "boost": sample_boost()
    }

# =========================================
# DASHBOARD COMPATIBLE API (IMPORTANT)
# =========================================

@app.get("/intraday-data")
def intraday_data():

    breakout_rows = []
    boost_rows = []

    # ----- तुझा breakout logic जिथे आहे तिथून data घे -----
    # उदाहरण (तू replace करशील तुझ्या actual function ने)
    breakout_data = DAY_STATE.get("breakout_list", [])

    for row in breakout_data[:10]:
        breakout_rows.append({
            "symbol": row["symbol"],
            "score": row["score"],
            "signal": row["signal"]
        })

    # ----- तुझा boost logic जिथे आहे तिथून data घे -----
    boost_data = DAY_STATE.get("boost_list", [])

    for row in boost_data[:10]:
        boost_rows.append({
            "symbol": row["symbol"],
            "boost": row["boost_score"],
            "r": row["r_factor"],
            "signal": row["signal"]
        })

    return {
        "breakout": breakout_rows,
        "boost": boost_rows
    }
