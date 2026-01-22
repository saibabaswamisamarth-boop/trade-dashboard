from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

MORNING_LEADERS = {}

def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_breakout(symbol, data):

    now = datetime.now(IST).strftime("%H:%M")

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    price = data.get("last_price", 0)
    vwap = data.get("average_price", price)
    volume = data.get("volume", 0)

    if not open_p or not price:
        return None

    move_open = pct(open_p, price)
    range_pct = pct(low_p, high_p)

    # -------- MORNING LEADER CAPTURE (9:15–9:45) --------
    if "09:15" <= now <= "09:45":
        if abs(move_open) > 1.2 and volume > 200000 and price > vwap:
            MORNING_LEADERS[symbol] = {
                "break_price": price,
                "time": now
            }

    # -------- Only track morning leaders after that --------
    if symbol not in MORNING_LEADERS:
        return None

    break_price = MORNING_LEADERS[symbol]["break_price"]

    rf_pct = pct(break_price, price)
    score = round(abs(rf_pct)) + 5

    signal = "BULLISH" if rf_pct > 0 else "BEARISH"

    return {
        "symbol": symbol,
        "score": score,
        "rf_pct": round(abs(rf_pct), 2),
        "signal": signal
    }
