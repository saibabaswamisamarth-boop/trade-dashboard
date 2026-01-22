def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_boost(symbol, data):

    ohlc = data.get("ohlc", {})

    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)

    price = data.get("last_price", 0)
    vwap = data.get("average_price", price)
    volume = data.get("volume", 0)

    if not open_p or not price or not high_p or not low_p:
        return None

    move_open = abs(pct(open_p, price))
    range_pct = abs(pct(low_p, high_p))
    vwap_dist = abs(pct(vwap, price))

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
