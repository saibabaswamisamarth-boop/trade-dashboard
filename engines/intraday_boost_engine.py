# engines/intraday_boost_engine.py

from datetime import datetime

# -------------------------
# HELPERS
# -------------------------

def pct_change(a, b):
    if a == 0:
        return 0
    return round(((b - a) / a) * 100, 2)


def candle_range(h, l):
    return abs(h - l)


def is_power_candle(o, h, l, c):
    body = abs(c - o)
    total = h - l
    if total == 0:
        return False
    return body / total > 0.8


# -------------------------
# MAIN ENGINE
# -------------------------

def process_intraday_boost(symbol, data, index_move_pct=0):

    ohlc = data.get("ohlc", {})
    depth = data.get("depth", {})

    open_p = ohlc.get("open", 0)
    high_p = ohlc.get("high", 0)
    low_p = ohlc.get("low", 0)
    close_p = data.get("last_price", 0)

    avg_price = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    buy_qty = sum(x.get("quantity", 0) for x in depth.get("buy", []))
    sell_qty = sum(x.get("quantity", 0) for x in depth.get("sell", []))

    # ======================
    # MARKET MODE
    # ======================
    if abs(index_move_pct) < 0.3:
        market_mode = "SIDEWAYS"
    else:
        market_mode = "TRENDING"

    score = 0
    notes = []

    # ======================
    # GAP FILTER (2)
    # ======================
    gap_pct = pct_change(data.get("prev_close", open_p), open_p)
    if abs(gap_pct) > 0.8:
        score += 2
        notes.append("GAP")

    # ======================
    # ORB (2)
    # ======================
    if close_p > high_p * 0.995:
        score += 2
        notes.append("ORB_UP")
    elif close_p < low_p * 1.005:
        score += 2
        notes.append("ORB_DOWN")

    # ======================
    # VWAP HOLD (2)
    # ======================
    if close_p > avg_price:
        score += 2
        notes.append("VWAP_HOLD")

    # ======================
    # POWER CANDLE (1)
    # ======================
    if is_power_candle(open_p, high_p, low_p, close_p):
        score += 1
        notes.append("POWER")

    # ======================
    # RANGE EXPANSION (2)
    # ======================
    if candle_range(high_p, low_p) > close_p * 0.015:
        score += 2
        notes.append("RANGE_EXP")

    # ======================
    # VOLUME SPIKE (2)
    # ======================
    if volume > 1_500_000:
        score += 2
        notes.append("VOLUME")

    # ======================
    # LIQUIDITY ABSORPTION (2)
    # ======================
    if buy_qty > sell_qty * 1.2:
        score += 2
        notes.append("ABSORB")

    # ======================
    # RELATIVE STRENGTH (2)
    # ======================
    stock_move = pct_change(open_p, close_p)
    if stock_move > index_move_pct:
        score += 2
        notes.append("RS")

    # ======================
    # SMART TIME (1)
    # ======================
    now = datetime.now().strftime("%H:%M")
    if "09:20" <= now <= "10:30" or "13:45" <= now <= "14:45":
        score += 1
        notes.append("TIME")

    # ======================
    # SIDEWAYS FILTER
    # ======================
    if market_mode == "SIDEWAYS":
        score = min(score, 10)

    # ======================
    # FINAL FILTER
    # ======================
    if score < 7:
        return None

    if score >= 15:
        signal = "ELITE"
    elif score >= 11:
        signal = "STRONG"
    else:
        signal = "WATCH"

    return {
        "symbol": symbol,
        "boost_score": score,
        "signal": signal,
        "r_factor": round(volume / 1_000_000, 2),
        "volume": volume,
        "notes": ",".join(notes),
        "market_mode": market_mode,
        "time": now
    }
