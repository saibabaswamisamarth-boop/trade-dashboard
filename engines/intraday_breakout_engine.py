def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_breakout(symbol, data):
    ohlc = data.get("ohlc", {})
    depth = data.get("depth", {})

    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    price = data.get("last_price", 0)
    volume = data.get("volume", 0)

    if not open_p or not price:
        return None

    # --- Notebook Logic Simulation ---

    # 1. New High / Low break
    nh = 2 if price >= high_p or price <= low_p else 0

    # 2. Candle strength
    body = abs(pct(open_p, price))
    cs = 1.5 if body > 0.4 else 0

    # 3. Volume spike
    vol = 2 if volume > 800000 else 0

    # 4. Buyer seller imbalance
    bids = sum([b.get("quantity", 0) for b in depth.get("buy", [])])
    asks = sum([a.get("quantity", 0) for a in depth.get("sell", [])])
    bsi = 1.5 if bids > asks * 1.3 or asks > bids * 1.3 else 0

    # 5. Position build
    pb = 1 if body > 0.3 else 0

    # 6. Market sync (simple)
    mt = 1 if price > open_p else 0

    bs = nh + cs + vol + bsi + pb + mt

    signal = "BULLISH" if price > open_p else "BEARISH"

    return {
        "symbol": symbol,
        "score": round(bs, 2),
        "rf_pct": round(body * 5, 2),
        "signal": signal
    }
