def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_boost(symbol, data):
    ohlc = data.get("ohlc", {})
    depth = data.get("depth", {})

    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    price = data.get("last_price", 0)
    vwap = data.get("average_price", price)
    volume = data.get("volume", 0)

    if not open_p or not price:
        return None

    # 1. Daily range capacity
    range_pct = abs(pct(low_p, high_p))
    dc = 2 if range_pct > 2 else 0

    # 2. Big players
    bids = sum([b.get("quantity", 0) for b in depth.get("buy", [])])
    asks = sum([a.get("quantity", 0) for a in depth.get("sell", [])])
    bpi = 2 if bids > asks * 1.5 or asks > bids * 1.5 else 0

    # 3. VWAP distance
    vd = 1.5 if abs(pct(vwap, price)) > 0.3 else 0

    # 4. Volume power
    vp = 2 if volume > 1200000 else 0

    # 5. Volatility
    vol = 1.5 if range_pct > 3 else 0

    ibs = dc + bpi + vd + vp + vol

    signal = "BULLISH" if price > vwap else "BEARISH"

    return {
        "symbol": symbol,
        "score": round(ibs, 2),
        "r_factor": round(range_pct * 3, 2),
        "signal": signal
    }
