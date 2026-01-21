if abs(index_move_pct) < 0.3:
    market_mode = "SIDEWAYS"
# engines/intraday_boost_engine.py

def process_intraday_boost(symbol, data, index_move_pct=0):

    last_price = data.get("last_price", 0)
    open_price = data.get("ohlc", {}).get("open", last_price)
    volume = data.get("volume", 0)
    avg_price = data.get("average_price", last_price)

    # ======================
    # MARKET MODE
    # ======================
    if abs(index_move_pct) < 0.3:
        market_mode = "SIDEWAYS"
    else:
        market_mode = "TRENDING"

    # ======================
    # BASIC CALCULATIONS
    # ======================
    price_change_pct = ((last_price - open_price) / open_price) * 100 if open_price else 0
    r_factor = round(volume / 1_000_000, 2)

    boost_score = 0

    # ======================
    # CORE LOGIC
    # ======================

    if price_change_pct > 0.4:
        boost_score += 1

    if last_price > avg_price:
        boost_score += 1

    if r_factor > 1.2:
        boost_score += 1

    # SIDEWAYS MARKET PROTECTION
    if market_mode == "SIDEWAYS":
        boost_score = min(boost_score, 3)

    # FINAL FILTER
    if boost_score < 2:
        return None   # ❌ reject stock

    signal = "BULL" if price_change_pct > 0 else "BEAR"

    return {
        "symbol": symbol,
        "boost_score": boost_score,
        "r_factor": r_factor,
        "signal": signal,
        "volume": volume
    }
# engines/intraday_boost_engine.py
# ==========================================
# INTRADAY BOOST ENGINE – 20 POINT SYSTEM
# Trader / Smart Money Level Logic
# ==========================================

from datetime import datetime


# -------------------------
# HELPERS
# -------------------------

def pct_change(a, b):
    if a == 0:
        return 0
    return round(((b - a) / a) * 100, 2)


def candle_range(o, h, l):
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
    """
    Input:
      symbol: str
      data: NSE_EQ quote dict (Dhan)
      index_move_pct: NIFTY/BANKNIFTY % change (proxy)
    Output:
      Intraday Boost dict
    """

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

    score = 0
    notes = []

    # ==========================================
    # A. GAP FILTER (2)
    # ==========================================
    gap_pct = pct_change(data.get("prev_close", open_p), open_p)
    if abs(gap_pct) > 0.8:
        score += 2
        notes.append("GAP")

    # ==========================================
    # B. ORB – Opening Range Breakout (2)
    # (proxy using day high/low)
    # ==========================================
    if close_p > high_p * 0.995:
        score += 2
        notes.append("ORB_UP")
    elif close_p < low_p * 1.005:
        score += 2
        notes.append("ORB_DOWN")

    # ==========================================
    # C. VWAP RETEST + HOLD (2)
    # ==========================================
    if close_p > avg_price:
        score += 2
        notes.append("VWAP_HOLD")

    # ==========================================
    # D. POWER CANDLE – NO WICK (1)
    # ==========================================
    if is_power_candle(open_p, high_p, low_p, close_p):
        score += 1
        notes.append("POWER_CANDLE")

    # ==========================================
    # E. RANGE EXPANSION (2)
    # ==========================================
    if candle_range(open_p, high_p, low_p) > (avg_price * 0.015):
        score += 2
        notes.append("RANGE_EXP")

    # ==========================================
    # F. VOLUME × RANGE (2)
    # ==========================================
    if volume > 1_500_000:
        score += 2
        notes.append("VOLUME_SPIKE")

    # ==========================================
    # G. LIQUIDITY ABSORPTION (2)
    # ==========================================
    if buy_qty > sell_qty * 1.2:
        score += 2
        notes.append("BUY_ABSORPTION")

    # ==========================================
    # H. HIGHER TF ALIGNMENT (2)
    # (proxy: price above avg)
    # ==========================================
    if close_p > avg_price:
        score += 2
        notes.append("HTF_ALIGN")

    # ==========================================
    # I. RELATIVE STRENGTH VS INDEX (2)
    # ==========================================
    stock_move = pct_change(open_p, close_p)
    if stock_move > index_move_pct:
        score += 2
        notes.append("RS_STRONG")

    # ==========================================
    # J. SMART MONEY TIME ZONE (1)
    # ==========================================
    now = datetime.now().strftime("%H:%M")
    if "09:20" <= now <= "10:30" or "13:45" <= now <= "14:45":
        score += 1
        notes.append("SMART_TIME")

    # ==========================================
    # FINAL SIGNAL
    # ==========================================
    if score >= 15:
        signal = "ELITE"
    elif score >= 11:
        signal = "STRONG"
    elif score >= 7:
        signal = "WATCH"
    else:
        signal = "IGNORE"

    return {
        "symbol": symbol,
        "boost_score": score,
        "signal": signal,
        "r_factor": round(volume / 1_000_000, 2),
        "volume": volume,
        "notes": ",".join(notes),
        "time": now
    }


