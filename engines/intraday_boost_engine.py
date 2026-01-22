from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def now_hm():
    return datetime.now(IST).strftime("%H:%M")

def process_intraday_breakout(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    close_p = data.get("last_price", 0)
    vwap = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    if not open_p or not close_p:
        return None

    # -----------------------------
    # RANGE EXPANSION FROM OPEN
    # -----------------------------
    move_pct = ((close_p - open_p) / open_p) * 100
    move_pct = round(move_pct, 2)

    # Minimum 2% move (real breakout)
    if abs(move_pct) < 2:
        return None

    # VWAP confirmation
    bullish = close_p > vwap
    bearish = close_p < vwap

    if move_pct > 0 and not bullish:
        return None
    if move_pct < 0 and not bearish:
        return None

    # Volume filter
    if volume < 300000:
        return None

    direction = "BULLISH" if move_pct > 0 else "BEARISH"

    score = int(abs(move_pct)) + 5

    signal = f"{direction} {abs(move_pct)}%"

    return {
        "symbol": symbol,
        "boost_score": score,
        "signal": signal,
        "move_pct": abs(move_pct),
        "direction": direction,
        "break_time": now_hm()
    }


def process_intraday_boost(symbol, data):
    return None
