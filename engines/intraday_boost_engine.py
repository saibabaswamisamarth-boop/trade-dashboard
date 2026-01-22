from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def now_hm():
    return datetime.now(IST).strftime("%H:%M")


# -------------------------------------------------
# BREAKOUT ENGINE (LEFT PANEL)
# -------------------------------------------------
def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_boost(symbol, data):

    ohlc = data.get("ohlc", {})
    depth = data.get("depth", {})

    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    close_p = data.get("last_price", 0)

    vwap = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    buy_qty = sum(x.get("quantity", 0) for x in depth.get("buy", []))
    sell_qty = sum(x.get("quantity", 0) for x in depth.get("sell", []))

    if not open_p or not close_p:
        return None

    # ---------------------------------
    # 1️⃣ RANGE + MOVE (SCORE LOGIC)
    # ---------------------------------
    range_pct = abs(pct(low_p, high_p))
    move_pct = abs(pct(open_p, close_p))
    volume_factor = volume / 300000

    score = (
        range_pct * 1.2 +
        move_pct * 1.8 +
        volume_factor
    )
    score = round(score, 2)

    # ---------------------------------
    # 2️⃣ BUYER / SELLER IMBALANCE
    # ---------------------------------
    imbalance = (buy_qty - sell_qty) / max((buy_qty + sell_qty), 1)

    # ---------------------------------
    # 3️⃣ R FACTOR (% ACTIVITY POWER)
    # ---------------------------------
    r_factor = (
        range_pct * 1.5 +
        move_pct * 2 +
        volume_factor * 2 +
        abs(imbalance) * 100
    )
    r_factor = round(r_factor, 2)

    # ---------------------------------
    # 4️⃣ SIGNAL
    # ---------------------------------
    if imbalance > 0 and close_p > vwap:
        signal = "STRONG BULLISH"
    elif imbalance < 0 and close_p < vwap:
        signal = "STRONG BEARISH"
    elif close_p > vwap:
        signal = "BULLISH"
    else:
        signal = "BEARISH"

    return {
        "symbol": symbol,
        "score": score,         # LEFT COLUMN
        "r_factor": r_factor,   # SORTING COLUMN (%)
        "signal": signal
    }


