from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/pro-dashboard", response_class=HTMLResponse)
def pro_dashboard():
    return HTMLResponse(
        "<html><body style='background:black;color:white;text-align:center;'>"
        "<h1>Render Deployment Successful 🎉</h1>"
        "</body></html>"
    )
@app.get("/market-pulse")
def market_pulse():
    return [
        {
            "symbol": "RELIANCE",
            "last_price": 1413.6,
            "volume": 20392765,
            "status": "ACTIVE"
        }
    ]
FO_STOCKS = {
    "RELIANCE": 2885,
    "TCS": 11536,
    "INFY": 1594,
    "HDFCBANK": 1333,
    "ICICIBANK": 4963,
    "SBIN": 3045,
    "AXISBANK": 5900,
    "LT": 11483,
    "ITC": 1660,
    "BAJFINANCE": 317
}
from dhanhq import dhanhq
import os

def get_dhan_client():
    client_id = os.getenv("CLIENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")

    if not client_id or not access_token:
        raise Exception("Dhan ENV variables not set")

    return dhanhq(client_id, access_token)
@app.get("/fo-live-scan")
def fo_live_scan():

    dhan = get_dhan_client()
    results = []

    for symbol, sid in FO_STOCKS.items():
        try:
            quote = dhan.quote_data(
                securities={"NSE_EQ": [sid]}
            )

            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse:
                continue

            data = nse[str(sid)]
            ohlc = data.get("ohlc", {})

            last_price = data.get("last_price", 0)
            open_price = ohlc.get("open", 0)
            high_price = ohlc.get("high", 0)
            volume = data.get("volume", 0)
            avg_price = data.get("average_price", 1)

            # Market Pulse logic (simple + safe)
            price_strength = last_price > open_price
            breakout_zone = last_price > (high_price * 0.8)
            volume_spike = volume > (avg_price * 1000)

            score = sum([price_strength, breakout_zone, volume_spike])

            if score >= 2:
                results.append({
                    "symbol": symbol,
                    "last_price": last_price,
                    "volume": volume,
                    "score": score
                })

        except Exception as e:
            print(f"Error in {symbol}: {e}")

    # Top movers first
    results = sorted(results, key=lambda x: x["volume"], reverse=True)

    return results[:10]
