from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_boost(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    price = data.get("last_price", 0)
    vwap = data.get("average_price", price)

    if not open_p or not price:
        return None

    # 🔥 RUNNER LOGIC
    move_from_open = abs(pct(open_p, price))

    if price > open_p:
        expansion = abs(pct(open_p, high_p))
        signal = "BULLISH"
    else:
        expansion = abs(pct(open_p, low_p))
        signal = "BEARISH"

    vwap_dist = abs(pct(vwap, price))

    # 🔥 FINAL R FACTOR
    r_factor = (
        move_from_open * 3 +
        expansion * 4 +
        vwap_dist * 2
    )
    r_factor = round(r_factor, 2)

    boost = round(r_factor / 5, 2)

    return {
        "symbol": symbol,
        "score": boost,
        "r_factor": r_factor,
        "signal": signal
    }
