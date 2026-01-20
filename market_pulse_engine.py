from datetime import datetime

# =========================
# HELPERS
# =========================

def calc_pct_change(open_price, last_price):
    if open_price == 0:
        return 0
    return round(((last_price - open_price) / open_price) * 100, 2)

def calc_signal(last_price, open_price):
    return "BULL" if last_price > open_price else "BEAR"

def calc_vwap_delta(avg_price, last_price):
    return round(last_price - avg_price, 2)

def calc_imbalance(depth):
    buy_qty = sum(x.get("quantity", 0) for x in depth.get("buy", []))
    sell_qty = sum(x.get("quantity", 0) for x in depth.get("sell", []))
    return buy_qty - sell_qty

def calc_r_factor(volume, base_volume=1_000_000):
    return round(volume / base_volume, 2)

def pulse_strength(score):
    if score >= 4:
        return "STRONG"
    elif score >= 2:
        return "MEDIUM"
    return "WEAK"

# =========================
# MAIN ENGINE
# =========================

def process_stock(symbol, data):

    ohlc = data.get("ohlc", {})
    depth = data.get("depth", {})

    last_price = data.get("last_price", 0)
    volume = data.get("volume", 0)
    avg_price = data.get("average_price", last_price)
    open_price = ohlc.get("open", last_price)

    pct_change = calc_pct_change(open_price, last_price)
    signal = calc_signal(last_price, open_price)
    vwap_delta = calc_vwap_delta(avg_price, last_price)
    imbalance = calc_imbalance(depth)
    r_factor = calc_r_factor(volume)

    # =========================
    # SCORING
    # =========================
    score = 0
    score += pct_change > 0
    score += vwap_delta > 0
    score += imbalance > 0
    score += r_factor > 1

    pulse = pulse_strength(score)

    return {
        "symbol": symbol,
        "signal": signal,
        "price_change_pct": pct_change,
        "vwap_delta": vwap_delta,
        "imbalance": imbalance,
        "r_factor": r_factor,
        "volume": volume,
        "pulse_score": score,
        "pulse": pulse,
        "time": datetime.now().strftime("%H:%M")
    }
