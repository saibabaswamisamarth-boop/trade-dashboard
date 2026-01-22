from datetime import datetime

def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_breakout(symbol, data):

    # ✅ CORRECT LIVE FIELDS FROM DHAN
    open_p = data.get("open_price", 0)
    high_p = data.get("day_high", 0)
    low_p = data.get("day_low", 0)
    close_p = data.get("last_price", 0)

    if not open_p or not close_p or not high_p or not low_p:
        return None

    move_from_open = abs(pct(open_p, close_p))
    range_pct = abs(pct(low_p, high_p))

    # Direction + Expansion
    if close_p > open_p:
        expansion = abs(pct(open_p, high_p))
        signal = "BULLISH"
    else:
        expansion = abs(pct(open_p, low_p))
        signal = "BEARISH"

    # 🔥 REAL RF %
    rf_pct = (
        move_from_open * 3 +
        expansion * 4 +
        range_pct * 1.5
    )

    rf_pct = round(rf_pct, 2)
    score = round(rf_pct / 10, 1)

    return {
        "symbol": symbol,
        "score": score,
        "rf_pct": rf_pct,
        "signal": signal
    }
