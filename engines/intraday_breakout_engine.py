from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

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

    # ---- RUNNER LOGIC ----
    move_from_open = abs(pct(open_p, price))

    if price > open_p:
        expansion = abs(pct(open_p, high_p))
        signal = "BULLISH"
    else:
        expansion = abs(pct(open_p, low_p))
        signal = "BEARISH"

    rf_pct = (move_from_open * 5) + (expansion * 5)
    rf_pct = round(rf_pct, 2)

    score = round(rf_pct / 10, 0)

    return {
        "symbol": symbol,
        "score": score,
        "rf_pct": rf_pct,
        "signal": signal
    }
