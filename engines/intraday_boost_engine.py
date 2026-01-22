def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_boost(symbol, data):

    # ✅ CORRECT LIVE FIELDS FROM DHAN
    open_p = data.get("open_price", 0)
    high_p = data.get("day_high", 0)
    low_p = data.get("day_low", 0)
    price = data.get("last_price", 0)
    vwap = data.get("average_price", price)
    volume = data.get("volume", 0)

    if not open_p or not price or not high_p or not low_p:
        return None

    move_open = abs(pct(open_p, price))
    range_pct = abs(pct(low_p, high_p))
    vwap_dist = abs(pct(vwap, price))

    # 🔥 PURE ACTIVITY BASED R-FACTOR
    r_factor = (
        move_open * 2 +
        range_pct * 1.5 +
        vwap_dist * 2 +
        (volume / 500000)
    )

    r_factor = round(r_factor, 2)
    score = round(r_factor / 5, 2)

    signal = "BULLISH" if price > vwap else "BEARISH"

    return {
        "symbol": symbol,
        "score": score,
        "r_factor": r_factor,
        "signal": signal
    }
