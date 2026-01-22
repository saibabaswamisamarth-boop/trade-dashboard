# Sustained Trend Boost Engine (Notebook Logic)

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

# Day memory — sustain stocks साठी
BOOST_MEMORY = {}


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
    ltp = data.get("last_price", 0)
    vwap = data.get("average_price", ltp)
    volume = data.get("volume", 0)

    buy_qty = sum(x.get("quantity", 0) for x in depth.get("buy", []))
    sell_qty = sum(x.get("quantity", 0) for x in depth.get("sell", []))

    if not open_p or not ltp:
        return None

    # ------------------------------------------
    # 1️⃣ Move from Open (Trend strength)
    # ------------------------------------------
    move_open_pct = abs(pct(open_p, ltp))

    # ------------------------------------------
    # 2️⃣ VWAP Sustain (trend side)
    # ------------------------------------------
    vwap_side = 1 if ltp > vwap else -1

    # ------------------------------------------
    # 3️⃣ Buyer/Seller Imbalance
    # ------------------------------------------
    imbalance = (buy_qty - sell_qty) / max((buy_qty + sell_qty), 1)

    # ------------------------------------------
    # 4️⃣ Volume Power (average पेक्षा जास्त का?)
    # ------------------------------------------
    volume_factor = volume / 300000

    # ------------------------------------------
    # 5️⃣ Range Expansion
    # ------------------------------------------
    range_pct = abs(pct(low_p, high_p))

    # ------------------------------------------
    # Qualification (Notebook style)
    # ------------------------------------------
    if move_open_pct < 1.8 or volume_factor < 1.2:
        return None

    # ------------------------------------------
    # Memory lock (sustain stocks)
    # ------------------------------------------
    if symbol not in BOOST_MEMORY:
        if len(BOOST_MEMORY) < 15:  # first leaders capture
            BOOST_MEMORY[symbol] = {
                "direction": "BULLISH" if vwap_side > 0 else "BEARISH"
            }

    if symbol in BOOST_MEMORY:

        direction = BOOST_MEMORY[symbol]["direction"]

        # --------------------------------------
        # R-Factor = Sustained power
        # --------------------------------------
        r_factor = round(
            move_open_pct * 2 +
            range_pct * 1.5 +
            volume_factor * 2 +
            abs(imbalance) * 120,
            2
        )

        score = round(
            move_open_pct +
            volume_factor +
            range_pct,
            2
        )

        if imbalance > 0 and vwap_side > 0:
            signal = "STRONG BULLISH"
        elif imbalance < 0 and vwap_side < 0:
            signal = "STRONG BEARISH"
        elif vwap_side > 0:
            signal = "BULLISH"
        else:
            signal = "BEARISH"

        return {
            "symbol": symbol,
            "boost": score,
            "r_factor": r_factor,
            "signal": signal
        }

    return None
