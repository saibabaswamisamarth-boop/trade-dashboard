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
FO_STOCKS_FULL = {
    "ADANIENT": 25,
    "ADANIPORTS": 15083,
    "APOLLOHOSP": 157,
    "ASIANPAINT": 236,
    "AXISBANK": 5900,
    "BAJAJ-AUTO": 16669,
    "BAJFINANCE": 317,
    "BAJAJFINSV": 16675,
    "BPCL": 526,
    "BHARTIARTL": 10604,
    "BRITANNIA": 547,
    "CIPLA": 694,
    "COALINDIA": 20374,
    "DIVISLAB": 10940,
    "DRREDDY": 881,
    "EICHERMOT": 910,
    "GRASIM": 1232,
    "HCLTECH": 7229,
    "HDFCBANK": 1333,
    "HDFCLIFE": 467,
    "HEROMOTOCO": 1348,
    "HINDALCO": 1363,
    "HINDUNILVR": 1394,
    "ICICIBANK": 4963,
    "INDUSINDBK": 5258,
    "INFY": 1594,
    "ITC": 1660,
    "JSWSTEEL": 11723,
    "KOTAKBANK": 1922,
    "LT": 11483,
    "M&M": 2031,
    "MARUTI": 10999,
    "NESTLEIND": 17963,
    "NTPC": 11630,
    "ONGC": 2475,
    "POWERGRID": 14977,
    "RELIANCE": 2885,
    "SBIN": 3045,
    "SUNPHARMA": 3351,
    "TATAMOTORS": 3456,
    "TATASTEEL": 3499,
    "TCS": 11536,
    "TECHM": 13538,
    "TITAN": 3506,
    "ULTRACEMCO": 11532,
    "UPL": 11287,
    "WIPRO": 3787
}
from fastapi.responses import HTMLResponse

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard():
    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>F&O Live Scanner</title>
<meta http-equiv="refresh" content="10">
<style>
body {
  background:#0b1220;
  color:#e5e7eb;
  font-family: Arial;
}
.container {
  width:90%;
  margin:auto;
}
h1 {
  text-align:center;
  margin:20px 0;
}
table {
  width:100%;
  border-collapse:collapse;
}
th, td {
  padding:12px;
  border-bottom:1px solid #1f2937;
  text-align:center;
}
th {
  background:#0f172a;
}
.badge {
  padding:4px 12px;
  border-radius:20px;
  font-weight:bold;
}
.green {
  background:#064e3b;
  color:#34d399;
}
.yellow {
  background:#78350f;
  color:#facc15;
}
</style>
</head>

<body>
<div class="container">
  <h1>🔥 F&O Live Market Pulse</h1>
  <table id="tbl">
    <tr>
      <th>Symbol</th>
      <th>Last Price</th>
      <th>Volume</th>
      <th>Strength</th>
    </tr>
  </table>
</div>

<script>
async function loadData(){
  const r = await fetch('/fo-live-scan');
  const data = await r.json();

  let rows = `
    <tr>
      <th>Symbol</th>
      <th>Last Price</th>
      <th>Volume</th>
      <th>Strength</th>
    </tr>
  `;

  data.forEach(x => {
    let badge = x.score == 3
      ? '<span class="badge green">STRONG</span>'
      : '<span class="badge yellow">MEDIUM</span>';

    rows += `
      <tr>
        <td>${x.symbol}</td>
        <td>${x.last_price}</td>
        <td>${x.volume}</td>
        <td>${badge}</td>
      </tr>
    `;
  });

  document.getElementById("tbl").innerHTML = rows;
}

loadData();
</script>
</body>
</html>
"""
    return HTMLResponse(html)
