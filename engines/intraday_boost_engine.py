from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
STATE = {}

def now_hm():
    return datetime.now(IST).strftime("%H:%M")

def sum_qty(levels):
    return sum(x.get("quantity", 0) for x in levels)

def best_prices(levels, side):
    if not levels:
        return 0
    prices = [x.get("price", 0) for x in levels if x.get("price")]
    if not prices:
        return 0
    return max(prices) if side == "buy" else min(prices)

def process_intraday_breakout(symbol, data):

    ohlc = data.get("ohlc", {})
    depth = data.get("depth", {})

    open_p  = ohlc.get("open", 0)
    high_p  = ohlc.get("high", 0)
    low_p   = ohlc.get("low", 0)
    close_p = data.get("last_price", 0)

    vwap   = data.get("average_price", close_p)
    volume = data.get("volume", 0)

    if not all([open_p, high_p, low_p, close_p]):
        return None

    now = now_hm()
    if now < "09:25":
        return None

    # =======================================
    # 🔷 STAGE 1 — LOGIC QUALIFICATION
    # =======================================

    # 1) VWAP side
    bullish = close_p > vwap
    bearish = close_p < vwap
    if not (bullish or bearish):
        return None

    # 2) Candle strength
    rng = high_p - low_p
    if rng == 0:
        return None
    body = abs(close_p - open_p)
    if body / rng < 0.5:
        return None

    # 3) Meaningful move from open
    move_from_open = abs((close_p - open_p) / open_p) * 100
    if move_from_open < 0.35:
        return None

    # 4) Buyer / Seller Imbalance
    buy_qty  = sum_qty(depth.get("buy", []))
    sell_qty = sum_qty(depth.get("sell", []))

    if bullish and buy_qty < sell_qty * 1.3:
        return None
    if bearish and sell_qty < buy_qty * 1.3:
        return None

    # 5) Bid-Ask spread (tight spread only)
    best_bid = best_prices(depth.get("buy", []), "buy")
    best_ask = best_prices(depth.get("sell", []), "sell")
    if best_bid and best_ask:
        spread_pct = ((best_ask - best_bid) / best_bid) * 100
        if spread_pct > 0.25:
            return None

    # 6) Volume vs Average (RVOL proxy)
    if volume < 200_000:
        return None

    # =======================================
    # 🔷 STAGE 2 — FIRST BREAKOUT CAPTURE
    # =======================================

    if symbol not in STATE:
        if bullish and close_p >= high_p * 0.998:
            STATE[symbol] = {
                "break_price": close_p,
                "break_time": now,
                "direction": "BULLISH"
            }
        elif bearish and close_p <= low_p * 1.002:
            STATE[symbol] = {
                "break_price": close_p,
                "break_time": now,
                "direction": "BEARISH"
            }
        else:
            return None

    state = STATE[symbol]

    # =======================================
    # 🔷 STAGE 3 — MOVE AFTER BREAKOUT
    # =======================================

    base = state["break_price"]
    move_pct = ((close_p - base) / base) * 100
    move_pct = round(move_pct, 2)

    # =======================================
    # SCORE
    # =======================================

    score = 6
    if abs(move_pct) >= 0.5:
        score += 2
    if abs(move_pct) >= 1.0:
        score += 2
    if abs(move_pct) >= 2.0:
        score += 3

    direction = state["direction"]
    signal = f"{direction} {abs(move_pct)}% @{state['break_time']}"

    return {
        "symbol": symbol,
        "boost_score": score,
        "signal": signal,
        "move_pct": abs(move_pct),
        "direction": direction,
        "break_time": state["break_time"]
    }


def process_intraday_boost(symbol, data):
    return None
