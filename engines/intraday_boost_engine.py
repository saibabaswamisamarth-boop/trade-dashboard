from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 10
    
def process_intraday_boost(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    price = data.get("last_price", 0)
    vwap = data.get("average_price", price)
    volume = data.get("volume", 0)

    if not open_p or not price:
        return None

    move = abs(pct(open_p, price))
    range_pct = abs(pct(low_p, high_p))
    vwap_dist = abs(pct(vwap, price))

    activity = move + range_pct + vwap_dist

    # 🔥 REAL R FACTOR %
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

