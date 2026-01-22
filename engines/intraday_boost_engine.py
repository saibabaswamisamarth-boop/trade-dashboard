# engines/intraday_boost_engine.py

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# ============================
# BREAKOUT MEMORY
# ============================
BREAKOUT_STATE = {}

def now_hm():
    return datetime.now(IST).strftime("%H:%M")

# ============================
# INTRADAY BREAKOUT ENGINE
# ============================
def process_intraday_breakout(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    close_p = data.get("last_price", 0)

    vwap = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    if not all([open_p, high_p, low_p, close_p]):
        return None

    now = now_hm()

    # ⏱️ Only after 9:25
    if now < "09:25":
        return None

    # ============================
    # BASE RANGE (OPENING RANGE PROXY)
    # ============================
    base_high = max(open_p, high_p)
    base_low = min(open_p, low_p)

    bullish_break = close_p > base_high * 1.001
    bearish_break = close_p < base_low * 0.999

    if not (bullish_break or bearish_break):
        return None

    # ============================
    # VWAP FILTER (MANDATORY)
    # ============================
    if bullish_break and close_p < vwap:
        return None
    if bearish_break and close_p > vwap:
        return None

    # ============================
    # FIRST BREAKOUT CAPTURE
    # ============================
    if symbol not in BREAKOUT_STATE:
        BREAKOUT_STATE[symbol] = {
            "break_price": close_p,
            "break_time": now,
            "direction": "BULLISH" if bullish_break else "BEARISH"
        }

    state = BREAKOUT_STATE[symbol]
    base_price = state["break_price"]

    # ============================
    # MOVE % AFTER BREAKOUT
    # ============================
    move_pct = round(
        ((close_p - base_price) / base_price) * 100,
        2
    )

    # ============================
    # SCORE (FORMING → STRONG)
    # ============================
    score = 3  # breakout detected

    if abs(move_pct) >= 0.5:
        score += 2
    if abs(move_pct) >= 1.0:
        score += 2
    if abs(move_pct) >= 2.0:
        score += 3

    if volume > 300_000:
        score += 1

    direction = state["direction"]

    signal = f"{direction} {abs(move_pct)}% @{state['break_time']}"

    return {
        "symbol": symbol,
        "boost_score": score,
        "signal": signal,
        "move_pct": abs(move_pct),
        "direction": direction,
        "break_time": state["break_time"]
    }


# ============================
# Intraday Boost (OFF NOW)
# ============================
def process_intraday_boost(symbol, data):
    return None
