from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def now_hm():
    return datetime.now(IST).strftime("%H:%M")


# -------------------------------------------------
# BREAKOUT ENGINE (LEFT PANEL)
# -------------------------------------------------
def process_intraday_breakout(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    close_p = data.get("last_price", 0)
    vwap = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    if not open_p or not close_p:
        return None

    move_pct = ((close_p - open_p) / open_p) * 100
    move_pct = round(move_pct, 2)

    # Real breakout filter
    if abs(move_pct) < 2:
        return None

    # VWAP confirmation
    if move_pct > 0 and close_p < vwap:
        return None
    if move_pct < 0 and close_p > vwap:
        return None

    # Volume filter
    if volume < 300000:
        return None

    direction = "BULLISH" if move_pct > 0 else "BEARISH"
    score = int(abs(move_pct)) + 5

    signal = f"{direction} {abs(move_pct)}%"

    return {
        "symbol": symbol,
        "score": score,
        "signal": signal,
        "move_pct": abs(move_pct),
        "direction": direction,
        "break_time": now_hm()
    }


# -------------------------------------------------
# BOOST ENGINE (RIGHT PANEL — R FACTOR)
# -------------------------------------------------
def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_boost(symbol, data):

    ohlc = data.get("ohlc", {})
    depth = data.get("depth", {})

    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    close_p = data.get("last_price", 0)

    vwap = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    buy_qty = sum(x.get("quantity", 0) for x in depth.get("buy", []))
    sell_qty = sum(x.get("quantity", 0) for x in depth.get("sell", []))

    if not open_p or not close_p:
        return None

    # 1. Range Expansion
    range_pct = abs(pct(low_p, high_p))

    # 2. Move From Open
    move_pct = abs(pct(open_p, close_p))

    # 3. Volume Power
    volume_factor = volume / 300000

    # 4. Buyer/Seller Imbalance
    imbalance = (buy_qty - sell_qty) / max((buy_qty + sell_qty), 1)

    # 5. R-Factor Calculation
    r_factor = (
        range_pct * 1.5 +
        move_pct * 2 +
        volume_factor * 2 +
        abs(imbalance) * 100
    )

    r_factor = round(r_factor, 2)

    # Signal logic
    if imbalance > 0 and close_p > vwap:
        signal = "STRONG BULLISH"
    elif imbalance < 0 and close_p < vwap:
        signal = "STRONG BEARISH"
    elif close_p > vwap:
        signal = "BULLISH"
    else:
        signal = "BEARISH"

    return {
        "symbol": symbol,
        "boost": r_factor,
        "r_factor": r_factor,
        "signal": signal
    }
