def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_breakout(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    price = data.get("last_price", 0)

    if not open_p or not price:
        return None

    move = abs(pct(open_p, price))          # real move %
    range_pct = abs(pct(low_p, high_p))    # full day range %

    if price >= open_p:
        signal = "BULLISH"
    else:
        signal = "BEARISH"

    # 🔥 Correct RF calculation (ratio, not addition)
    rf_pct = (move / max(range_pct, 0.01)) * 100
    rf_pct = round(rf_pct, 2)

    score = round(move, 2)

    return {
        "symbol": symbol,
        "score": score,
        "rf_pct": rf_pct,
        "signal": signal
    }
