from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# Morning breakout memory (TOP 10 sustain साठी)
MORNING_MEMORY = {}


def now_hm():
    return datetime.now(IST).strftime("%H:%M")


def pct(a, b):
    if a == 0:
        return 0
    return ((b - a) / a) * 100


def process_intraday_breakout(symbol, data):

    ohlc = data.get("ohlc", {})
    open_p = ohlc.get("open", 0)
    ltp = data.get("last_price", 0)
    vwap = data.get("average_price", ltp)
    volume = data.get("volume", 0)

    if not open_p or not ltp:
        return None

    time_now = now_hm()

    # ---------------------------------------------------------
    # 🔴 STEP 1 — 9:20 नंतर FIRST REAL BREAKOUT पकड
    # ---------------------------------------------------------
    if symbol not in MORNING_MEMORY:

        move_from_open = pct(open_p, ltp)

        # Real move + volume + VWAP confirmation
        if abs(move_from_open) > 2 and volume > 300000:
            MORNING_MEMORY[symbol] = {
                "break_price": ltp,
                "break_time": time_now,
                "direction": "BULLISH" if ltp > vwap else "BEARISH"
            }

    # ---------------------------------------------------------
    # 🟢 STEP 2 — Breakout price पासून movement calculate
    # ---------------------------------------------------------
    if symbol in MORNING_MEMORY:

        bp = MORNING_MEMORY[symbol]["break_price"]
        direction = MORNING_MEMORY[symbol]["direction"]
        break_time = MORNING_MEMORY[symbol]["break_time"]

        move_pct = abs(pct(bp, ltp))
        move_pct = round(move_pct, 2)

        score = int(move_pct) + 5

        signal = f"{direction} {move_pct}% @ {break_time}"

        return {
            "symbol": symbol,
            "score": score,
            "signal": signal,
            "move_pct": move_pct
        }

    return None
