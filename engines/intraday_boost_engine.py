# engines/intraday_boost_engine.py

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

BREAKOUT_STATE = {}

def now_hm():
    return datetime.now(IST).strftime("%H:%M")

def process_intraday_breakout(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    close_p = data.get("last_price", 0)

    vwap = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    if not all([open_p, close_p]):
        return None

    now = now_hm()
    if now < "09:25":
        return None

    # -------------------------------
    # DIRECTION (VWAP BASED)
    # -------------------------------
    bullish = close_p > vwap
    bearish = close_p < vwap

    if not (bullish or bearish):
        return None

    # -------------------------------
    # OPENING MOVE (BREAKOUT SEED)
    # -------------------------------
    move_from_open = ((close_p - open_p) / open_p) * 100

    if abs(move_from_open) < 0.25:
        return None   # too flat

    # -------------------------------
    # FIRST TIME SEEN
    # -------------------------------
    if symbol not in BREAKOUT_STATE:
        BREAKOUT_STATE[symbol] = {
            "base_price": close_p,
            "time": now,
            "direction": "BULLISH" if bullish else "BEARISH"
        }

    state = BREAKOUT_STATE[symbol]
    base_price = state["base_price"]

    # -------------------------------
    # MOVE AFTER BREAKOUT
    # -------------------------------
    move_after = ((close_p - base_price) / base_price) * 100
    move_after = round(move_after, 2)

    # -------------------------------
    # SCORE SYSTEM (FORMING → STRONG)
    # -------------------------------
    score = 3  # candidate

    if abs(move_after) >= 0.5:
        score += 2
    if abs(move_after) >= 1.0:
        score += 2
    if abs(move_after) >= 2.0:
        score += 3

    if volume > 200_000:
        score += 1

    direction = state["direction"]
    signal = f"{direction} {round(abs(move_after),2)}% @{state['time']}"

    return {
        "symbol": symbol,
        "boost_score": score,
        "signal": signal,
        "move_pct": abs(move_after),
        "direction": direction,
        "break_time": state["time"]
    }


# Right panel OFF
def process_intraday_boost(symbol, data):
    return None
