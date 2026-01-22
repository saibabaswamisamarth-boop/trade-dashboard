def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_boost(symbol, data):

    open_p = data.get("open_price", 0)
high_p = data.get("day_high", 0)
low_p = data.get("day_low", 0)

    if not open_p or not price:
        return None

    move = abs(pct(open_p, price))
    range_pct = abs(pct(low_p, high_p))
    vwap_dist = abs(pct(vwap, price))

    activity = move + vwap_dist

    # 🔥 Correct R-Factor (ratio)
    r_factor = (activity / max(range_pct, 0.01)) * 100
    r_factor = round(r_factor, 2)

    score = round(activity, 2)
    signal = "BULLISH" if price > vwap else "BEARISH"

    return {
        "symbol": symbol,
        "score": score,
        "r_factor": r_factor,
        "signal": signal
    }




