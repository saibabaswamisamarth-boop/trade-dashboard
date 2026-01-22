# engines/intraday_breakout_engine.py

def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_breakout(symbol, data):
    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    close_p = data.get("last_price", 0)
    vwap = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    if not open_p or not close_p:
        return None

    move_pct = round(pct(open_p, close_p), 2)

    # filters
    if abs(move_pct) < 2:
        return None
    if volume < 300000:
        return None

    if move_pct > 0 and close_p < vwap:
        return None
    if move_pct < 0 and close_p > vwap:
        return None

    direction = "BULLISH" if move_pct > 0 else "BEARISH"

    score = int(abs(move_pct)) + 5
    signal = f"{direction} {abs(move_pct)}%"

    return {
        "symbol": symbol,
        "score": score,
        "signal": signal,
        "move_pct": abs(move_pct)
    }
