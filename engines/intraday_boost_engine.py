# engines/intraday_boost_engine.py

# =================================================
# INTRADAY BREAKOUT (SAFE PLACEHOLDER)
# =================================================

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

    # VWAP mandatory
    if close_p <= vwap:
        return None

    # Simple breakout condition
    if close_p > high_p * 0.995 and volume > 300_000:
        return {
            "symbol": symbol,
            "boost_score": 5,
            "signal": "FORMING",
            "move_pct": 0.0
        }

    return None


# =================================================
# INTRADAY BOOST – NEW LOGIC (IMBALANCE BASED)
# =================================================

def process_intraday_boost(symbol, data):

    ohlc = data.get("ohlc", {})
    depth = data.get("depth", {})

    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    close_p = data.get("last_price", 0)

    vwap = data.get("average_price", close_p)
    volume = data.get("volume", 0)
    prev_close = data.get("prev_close", open_p)

    if not all([open_p, high_p, low_p, close_p]):
        return None

    # BUY / SELL IMBALANCE
    buy_qty = sum(x.get("quantity", 0) for x in depth.get("buy", []))
    sell_qty = sum(x.get("quantity", 0) for x in depth.get("sell", []))

    if sell_qty == 0:
        imbalance = 2
    else:
        imbalance = buy_qty / sell_qty

    # VWAP FILTER
    above_vwap = close_p > vwap
    below_vwap = close_p < vwap

    # CANDLE STRENGTH
    body = abs(close_p - open_p)
    full = high_p - low_p
    if full == 0:
        return None

    body_ratio = body / full
    strong_candle = body_ratio >= 0.6

    # GAP FILTER
    gap_pct = abs(open_p - prev_close) / prev_close * 100
    gap_ok = gap_pct < 2.5 or volume > 1_000_000

    # SCORE (R)
    R = 0

    if imbalance >= 1.5:
        R += 2
    elif imbalance >= 1.2:
        R += 1

    if strong_candle:
        R += 2

    if above_vwap or below_vwap:
        R += 2

    if gap_ok:
        R += 1

    if R < 4:
        return None

    # DIRECTION
    if above_vwap and close_p > open_p:
        direction = "BULLISH"
    elif below_vwap and close_p < open_p:
        direction = "BEARISH"
    else:
        return None

    if R >= 7:
        signal = f"STRONG {direction}"
    else:
        signal = direction

    return {
        "symbol": symbol,
        "boost_score": R,
        "r_factor": round(imbalance, 2),
        "signal": signal,
    }
