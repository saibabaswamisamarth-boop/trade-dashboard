from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def now_hm():
    return datetime.now(IST).strftime("%H:%M")

def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_breakout(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    close_p = data.get("last_price", 0)
    vwap = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    if not open_p or not close_p:
        return None

    move_pct = round(pct(open_p, close_p), 2)

    if abs(move_pct) < 2:
        return None

    if move_pct > 0 and close_p < vwap:
        return None
    if move_pct < 0 and close_p > vwap:
        return None

    if volume < 300000:
        return None

    direction = "BULLISH" if move_pct > 0 else "BEARISH"
    score = int(abs(move_pct)) + 5

    return {
        "symbol": symbol,
        "score": score,
        "rf_pct": abs(move_pct),
        "signal": direction
    }
