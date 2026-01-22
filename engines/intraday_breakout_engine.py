from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 10


def process_intraday_breakout(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    close_p = data.get("last_price", 0)

    if not open_p or not close_p:
        return None

    move_from_open = abs(pct(open_p, close_p))
    full_range = abs(pct(low_p, high_p))

    if close_p > open_p:
        expansion = abs(pct(open_p, high_p))
        signal = "BULLISH"
    else:
        expansion = abs(pct(open_p, low_p))
        signal = "BEARISH"

    # 🔥 REAL RF %
    rf_pct = (move_from_open / max(full_range, 0.01)) * 100
    rf_pct = round(rf_pct, 2)

    score = round(move_from_open, 1)

    return {
        "symbol": symbol,
        "score": score,
        "rf_pct": rf_pct,
        "signal": signal
    }



