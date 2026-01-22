# engines/intraday_boost_engine.py

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

    # ✅ BASE RANGE (SAFE PROXY)
    base_high = max(open_p, high_p)
    base_low = min(open_p, low_p)

    # ✅ BREAKOUT CONDITION (SOFT)
    bullish = close_p > base_high * 0.995
    bearish = close_p < base_low * 1.005

    if not (bullish or bearish):
        return None

    # ✅ VWAP FILTER
    if bullish and close_p < vwap:
        return None
    if bearish and close_p > vwap:
        return None

    # ✅ MOVE % (LIVE, MEMORY FREE)
    move_pct = round(((close_p - open_p) / open_p) * 100, 2)

    # ✅ SCORE SYSTEM
    score = 2  # base forming

    if abs(move_pct) >= 0.5:
        score += 2
    if abs(move_pct) >= 1.0:
        score += 2
    if volume > 300_000:
        score += 1

    direction = "BULLISH" if bullish else "BEARISH"
    signal = f"{direction} {abs(move_pct)}%"

    return {
        "symbol": symbol,
        "boost_score": score,
        "signal": signal,
        "move_pct": abs(move_pct),
    }


# ============================
# Intraday Boost (OFF for now)
# ============================
def process_intraday_boost(symbol, data):
    return None
