# engines/intraday_boost_engine.py

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# ===============================
# MEMORY FOR BREAKOUT TRACKING
# ===============================
BREAKOUT_MEMORY = {}

def now_hm():
    return datetime.now(IST).strftime("%H:%M")

# ===============================
# INTRADAY BREAKOUT ENGINE
# ===============================
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

    # ⏱️ Time filter
    now = now_hm()
    if now < "09:20" or now > "10:30":
        return None

    # 📦 Base range (simple proxy)
    base_high = high_p
    base_low = low_p
    base_range = base_high - base_low
    if base_range <= 0:
        return None

    # 🔥 Breakout condition
    bullish = close_p > base_high * 0.998
    bearish = close_p < base_low * 1.002

    if not (bullish or bearish):
        return None

    # ⚖️ VWAP mandatory
    if bullish and close_p < vwap:
        return None
    if bearish and close_p > vwap:
        return None

    # 🔊 Volume filter
    if volume < 250_000:
        return None

    # 🕯️ Candle strength
    body = abs(close_p - open_p)
    full = high_p - low_p
    if full == 0:
        return None

    body_ratio = body / full
    if body_ratio < 0.6:
        return None

    # ===============================
    # MOVE TRACKING
    # ===============================
    if symbol not in BREAKOUT_MEMORY:
        BREAKOUT_MEMORY[symbol] = {
            "base_price": close_p,
            "time": now
        }

    base_price = BREAKOUT_MEMORY[symbol]["base_price"]
    move_pct = round(((close_p - base_price) / base_price) * 100, 2)

    # ===============================
    # SCORE SYSTEM
    # ===============================
    score = 5  # forming breakout base

    if abs(move_pct) >= 0.8:
        score += 2
    if abs(move_pct) >= 1.5:
        score += 3
    if abs(move_pct) >= 3:
        score += 5

    # Direction
    direction = "BULLISH" if bullish else "BEARISH"

    signal = f"{direction} {move_pct}%"

    return {
        "symbol": symbol,
        "boost_score": score,
        "signal": signal,
        "move_pct": abs(move_pct),
        "direction": direction
    }

# ===============================
# INTRADAY BOOST (KEEP SIMPLE NOW)
# ===============================
def process_intraday_boost(symbol, data):
    return None
