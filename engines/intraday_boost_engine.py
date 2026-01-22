def process_intraday_boost(symbol, data, index_move_pct=0, sector_trend=0):

    # ==========================
    # BASIC LIVE DATA
    # ==========================
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

    # ==========================
    # BUYER / SELLER IMBALANCE
    # ==========================
    buy_qty = sum(x.get("quantity", 0) for x in depth.get("buy", []))
    sell_qty = sum(x.get("quantity", 0) for x in depth.get("sell", []))

    if sell_qty == 0:
        imbalance = 2
    else:
        imbalance = buy_qty / sell_qty

    # ==========================
    # TREND ZONE (HH-HL / LL-LH)
    # ==========================
    bullish_structure = close_p > open_p and high_p > open_p
    bearish_structure = close_p < open_p and low_p < open_p

    # ==========================
    # CANDLE STRENGTH
    # ==========================
    body = abs(close_p - open_p)
    full = high_p - low_p
    if full == 0:
        return None

    body_ratio = body / full
    strong_candle = body_ratio >= 0.65

    # ==========================
    # GAP FILTER
    # ==========================
    gap_pct = abs(open_p - prev_close) / prev_close * 100
    gap_valid = gap_pct < 2.5 or volume > 1_000_000

    # ==========================
    # RANGE & VOLATILITY
    # ==========================
    today_range_pct = (high_p - low_p) / close_p * 100
    wild_stock = today_range_pct > 4.5

    # ==========================
    # VWAP FILTER (MANDATORY)
    # ==========================
    above_vwap = close_p > vwap
    below_vwap = close_p < vwap

    # ==========================
    # MARKET / SECTOR CONTEXT
    # ==========================
    market_support = index_move_pct >= 0
    sector_support = sector_trend >= 0

    # ==========================
    # R SCORE (RELATIVE POWER)
    # ==========================
    R = 0

    # imbalance
    if imbalance >= 1.5:
        R += 2
    elif imbalance >= 1.2:
        R += 1

    # trend structure
    if bullish_structure or bearish_structure:
        R += 2

    # candle strength
    if strong_candle:
        R += 2

    # vwap
    if above_vwap or below_vwap:
        R += 2

    # gap
    if gap_valid:
        R += 1

    # market / sector
    if market_support:
        R += 1
    if sector_support:
        R += 1

    # wild volatility penalty
    if wild_stock:
        R -= 1

    if R < 4:
        return None

    # ==========================
    # DIRECTION & SIGNAL
    # ==========================
    if bullish_structure and above_vwap:
        direction = "BULLISH"
    elif bearish_structure and below_vwap:
        direction = "BEARISH"
    else:
        return None

    if R >= 8:
        signal = f"STRONG {direction}"
    else:
        signal = direction

    return {
        "symbol": symbol,
        "boost_score": R,
        "r_factor": round(imbalance, 2),
        "signal": signal,
        "range_pct": round(today_range_pct, 2),
        "imbalance": round(imbalance, 2),
    }
