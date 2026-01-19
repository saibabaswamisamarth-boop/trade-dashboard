import time

CACHE = {
    "snapshot": {
        "data": None,
        "time": 0
    }
}
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
 {
    
}
INDEX_STOCKS = {
    "RELIANCE": 2885,
    "HDFCBANK": 1333,
    "ICICIBANK": 4963,
    "TCS": 11536,
    "INFY": 1594
}

NIFTY_WEIGHTS = {
    "RELIANCE": 10.8,
    "HDFCBANK": 8.9,
    "ICICIBANK": 7.6,
    "TCS": 3.9,
    "INFY": 3.7
}
from fastapi.responses import HTMLResponse
STOCKS = {
    "RELIANCE": 2885,
    "TCS": 11536,
    "INFY": 1594,
    "HDFCBANK": 1333,
    "ICICIBANK": 4963
}
from fastapi import FastAPI
from dhanhq import dhanhq

app = FastAPI()
@app.get("/health")
def health():
    return {
        "CLIENT_ID": bool(os.getenv("CLIENT_ID")),
        "ACCESS_TOKEN": bool(os.getenv("ACCESS_TOKEN"))
    }

import os

import os

CLIENT_ID = os.getenv("CLIENT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")



dhan = get_dhan_client()
quote = dhan.quote_data(...)


@app.get("/", response_class=HTMLResponse)
def pro_dashboard():
    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Trade Dashboard</title>
<meta http-equiv="refresh" content="10">
<style>
body { background:#0b1220; color:#e5e7eb; font-family:Arial }
.container { width:92%; margin:auto; }
h1 { text-align:center; margin:20px 0; }
.grid { display:grid; grid-template-columns: 1fr 1fr; gap:20px; }
.card { background:#111827; border-radius:14px; padding:16px; }
table { width:100%; border-collapse:collapse }
th, td { padding:10px; border-bottom:1px solid #1f2937; text-align:center }
th { background:#0f172a }
.badge { padding:4px 10px; border-radius:999px; font-weight:600 }
.green { background:#064e3b; color:#34d399 }
.red { background:#3f1d1d; color:#f87171 }
</style>
</head>

<body>
<div class="container">
<h1>🔥 Trade Dashboard</h1>

<div class="grid">
  <div class="card">
    <h3>Market Pulse</h3>
    <div id="mp"></div>
  </div>
  <div class="card">
    <h3>Index Mover</h3>
    <div id="im"></div>
  </div>
</div>

<div class="card" style="margin-top:20px;">
  <h3>F&O Scanner (Top 10)</h3>
  <div id="fo"></div>
</div>
</div>

<script>
async function load(){
  const r = await fetch('/snapshot');
  const d = await r.json();

  let mp = `<table><tr><th>Symbol</th><th>Price</th><th>Volume</th><th>Status</th></tr>`;
  d.market_pulse.forEach(x=>{
    mp += `<tr><td>${x.symbol}</td><td>${x.last_price}</td><td>${x.volume}</td>
           <td><span class="badge green">ACTIVE</span></td></tr>`;
  });
  mp += `</table>`;
  document.getElementById('mp').innerHTML = mp;

  let im = `<table><tr><th>Symbol</th><th>Change %</th><th>Impact</th></tr>`;
  d.index_mover.forEach(x=>{
    const cls = x.impact_score >= 0 ? 'green':'red';
    im += `<tr><td>${x.symbol}</td><td>${x["change_%"]}</td>
           <td><span class="badge ${cls}">${x.impact_score}</span></td></tr>`;
  });
  im += `</table>`;
  document.getElementById('im').innerHTML = im;

  let fo = `<table><tr><th>Symbol</th><th>Price</th><th>Volume</th><th>Strength</th></tr>`;
  d.fo_scanner.forEach(x=>{
    let label = x.score == 3
      ? '<span class="badge green">STRONG</span>'
      : '<span class="badge">MEDIUM</span>';

    fo += `<tr><td>${x.symbol}</td><td>${x.last_price}</td><td>${x.volume}</td><td>${label}</td></tr>`;
  });
  fo += `</table>`;
  document.getElementById('fo').innerHTML = fo;
}
load();
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)



@app.get("/quote/{security_id}")
def get_quote(security_id: int):
    data = dhan.quote_data(
        securities={
            "NSE_EQ": [security_id]
        }
    )
    return data
from datetime import datetime

@app.get("/market-pulse/{security_id}")
def market_pulse(security_id: int):

    quote = dhan.quote_data(
        securities={
            "NSE_EQ": [security_id]
        }
    )

    data = quote["data"]["data"]["NSE_EQ"][str(security_id)]

    last_price = data["last_price"]
    open_price = data["ohlc"]["open"]
    high_price = data["ohlc"]["high"]
    volume = data["volume"]
    avg_price = data["average_price"]

    # Simple rules
    price_strength = last_price > open_price
    breakout_zone = last_price > (high_price * 0.8)
    volume_spike = volume > (avg_price * 1000)  # rough logic

    score = sum([price_strength, breakout_zone, volume_spike])

    return {
        "security_id": security_id,
        "last_price": last_price,
        "volume": volume,
        "price_strength": price_strength,
        "breakout_zone": breakout_zone,
        "volume_spike": volume_spike,
        "market_pulse_active": score >= 2
    }
@app.get("/scan-market-pulse")
def scan_market_pulse():

    results = []

    for name, sid in STOCKS.items():
        try:
            quote = dhan.quote_data(
                securities={
                    "NSE_EQ": [sid]
                }
            )

            # SAFE extraction
            nse_data = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse_data:
                continue

            data = nse_data[str(sid)]

            ohlc = data.get("ohlc", {})
            last_price = data.get("last_price", 0)
            open_price = ohlc.get("open", 0)
            high_price = ohlc.get("high", 0)
            volume = data.get("volume", 0)
            avg_price = data.get("average_price", 1)

            price_strength = last_price > open_price
            breakout_zone = last_price > (high_price * 0.8)
            volume_spike = volume > (avg_price * 1000)

            score = sum([price_strength, breakout_zone, volume_spike])

            if score >= 2:
                results.append({
                    "symbol": name,
                    "security_id": sid,
                    "last_price": last_price,
                    "volume": volume,
                    "market_pulse": True
                })

        except Exception as e:
            # NEVER crash server
            print(f"Error in {name} ({sid}): {e}")

    return results
@app.get("/", response_class=HTMLResponse)
def dashboard_root():

    results = []

    for name, sid in STOCKS.items():
        try:
            quote = dhan.quote_data(
                securities={"NSE_EQ": [sid]}
            )

            nse_data = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse_data:
                continue

            data = nse_data[str(sid)]
            ohlc = data.get("ohlc", {})

            last_price = data.get("last_price", 0)
            open_price = ohlc.get("open", 0)
            high_price = ohlc.get("high", 0)
            volume = data.get("volume", 0)
            avg_price = data.get("average_price", 1)

            price_strength = last_price > open_price
            breakout_zone = last_price > (high_price * 0.8)
            volume_spike = volume > (avg_price * 1000)

            score = sum([price_strength, breakout_zone, volume_spike])

            if score >= 2:
                results.append((name, sid, last_price, volume))

        except:
            pass

    # HTML TABLE
    html = """
    <html>
    <head>
        <title>Market Pulse Dashboard</title>
        <meta http-equiv="refresh" content="10">
        <style>
            body { background:#0f172a; color:white; font-family:Arial }
            table { width:70%; margin:auto; border-collapse:collapse }
            th, td { padding:12px; border-bottom:1px solid #334155; text-align:center }
            th { background:#1e293b }
            tr:hover { background:#020617 }
            h1 { text-align:center }
        </style>
    </head>
    <body>
        <h1>🔥 Market Pulse Scanner</h1>
        <table>
            <tr>
                <th>Symbol</th>
                <th>Security ID</th>
                <th>Last Price</th>
                <th>Volume</th>
                <th>Status</th>
            </tr>
    """

    for r in results:
        html += f"""
        <tr>
            <td>{r[0]}</td>
            <td>{r[1]}</td>
            <td>{r[2]}</td>
            <td>{r[3]}</td>
            <td style="color:lime;">ACTIVE</td>
        </tr>
        """

    html += """
        </table>
    </body>
    </html>
    """

    return html
@app.get("/index-mover")
def index_mover():

    movers = []

    for symbol, sid in INDEX_STOCKS.items():
        try:
            quote = dhan.quote_data(
                securities={"NSE_EQ": [sid]}
            )

            nse_data = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse_data:
                continue

            data = nse_data[str(sid)]
            ohlc = data.get("ohlc", {})

            open_price = ohlc.get("open", 0)
            last_price = data.get("last_price", 0)

            if open_price == 0 or last_price == 0:
                continue

            pct_change = ((last_price - open_price) / open_price) * 100
            weight = NIFTY_WEIGHTS.get(symbol, 0)

            impact = pct_change * weight

            movers.append({
                "symbol": symbol,
                "last_price": last_price,
                "change_%": round(pct_change, 2),
                "weight": weight,
                "impact_score": round(impact, 2)
            })

        except Exception as e:
            # NEVER crash server
            print(f"Index mover error in {symbol}: {e}")

    movers = sorted(
        movers,
        key=lambda x: abs(x["impact_score"]),
        reverse=True
    )

    return movers
@app.get("/scan-fo-market-pulse")
def scan_fo_market_pulse():

    results = []

    for symbol, sid in FO_STOCKS.items():
        try:
            quote = dhan.quote_data(
                securities={"NSE_EQ": [sid]}
            )

            nse_data = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse_data:
                continue

            data = nse_data[str(sid)]
            ohlc = data.get("ohlc", {})

            last_price = data.get("last_price", 0)
            open_price = ohlc.get("open", 0)
            high_price = ohlc.get("high", 0)
            volume = data.get("volume", 0)
            avg_price = data.get("average_price", 1)

            # Market Pulse rules
            price_strength = last_price > open_price
            breakout_zone = last_price > (high_price * 0.8)
            volume_spike = volume > (avg_price * 1000)

            score = sum([price_strength, breakout_zone, volume_spike])

            if score >= 2:
                results.append({
                    "symbol": symbol,
                    "security_id": sid,
                    "last_price": last_price,
                    "volume": volume,
                    "score": score
                })

        except Exception as e:
            print(f"FO scan error {symbol}: {e}")

    # Top stocks first (by volume)
    results = sorted(results, key=lambda x: x["volume"], reverse=True)

    # Top 10 only
    return results[:10]
@app.get("/snapshot")
def snapshot():
    now = time.time()

    # 10 sec cache
    if CACHE["snapshot"]["data"] and now - CACHE["snapshot"]["time"] < 10:
        return CACHE["snapshot"]["data"]

    data = {
        "market_pulse": scan_market_pulse(),
        "index_mover": index_mover(),
        "fo_scanner": scan_fo_market_pulse()
    }

    CACHE["snapshot"]["data"] = data
    CACHE["snapshot"]["time"] = now

    return data

from fastapi.responses import HTMLResponse

@app.get("/", response_class=HTMLResponse)
def dashboard_root():

    html = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Trade Dashboard</title>
<meta http-equiv="refresh" content="10">
<style>
body { background:#0b1220; color:#e5e7eb; font-family:Arial }
.container { width:92%; margin:auto; }
h1 { text-align:center; margin:20px 0; }
.grid { display:grid; grid-template-columns: 1fr 1fr; gap:20px; }
.card { background:#111827; border-radius:14px; padding:16px; }
table { width:100%; border-collapse:collapse }
th, td { padding:10px; border-bottom:1px solid #1f2937; text-align:center }
th { background:#0f172a }
.badge { padding:4px 10px; border-radius:999px; font-weight:600 }
.green { background:#064e3b; color:#34d399 }
.red { background:#3f1d1d; color:#f87171 }
</style>
</head>

<body>
<div class="container">
<h1>🔥 Trade Dashboard</h1>

<div class="grid">
  <div class="card">
    <h3>Market Pulse</h3>
    <div id="mp"></div>
  </div>
  <div class="card">
    <h3>Index Mover</h3>
    <div id="im"></div>
  </div>
</div>

<div class="card" style="margin-top:20px;">
  <h3>F&O Scanner (Top 10)</h3>
  <div id="fo"></div>
</div>
</div>

<script>
async function load(){
  const r = await fetch('/snapshot');
  const d = await r.json();

  let mp = `<table><tr><th>Symbol</th><th>Price</th><th>Volume</th><th>Status</th></tr>`;
  d.market_pulse.forEach(x=>{
    mp += `<tr><td>${x.symbol}</td><td>${x.last_price}</td><td>${x.volume}</td>
           <td><span class="badge green">ACTIVE</span></td></tr>`;
  });
  mp += `</table>`;
  document.getElementById('mp').innerHTML = mp;

  let im = `<table><tr><th>Symbol</th><th>Change %</th><th>Impact</th></tr>`;
  d.index_mover.forEach(x=>{
    const cls = x.impact_score >= 0 ? 'green':'red';
    im += `<tr><td>${x.symbol}</td><td>${x["change_%"]}</td>
           <td><span class="badge ${cls}">${x.impact_score}</span></td></tr>`;
  });
  im += `</table>`;
  document.getElementById('im').innerHTML = im;

  let fo = `<table><tr><th>Symbol</th><th>Price</th><th>Volume</th><th>Strength</th></tr>`;
  d.fo_scanner.forEach(x=>{
    let label = x.score == 3
      ? '<span class="badge green">STRONG</span>'
      : '<span class="badge">MEDIUM</span>';

    fo += `<tr><td>${x.symbol}</td><td>${x.last_price}</td><td>${x.volume}</td><td>${label}</td></tr>`;
  });
  fo += `</table>`;
  document.getElementById('fo').innerHTML = fo;
}
load();
</script>
</body>
</html>
"""
    return HTMLResponse(content=html)
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from dhanhq import dhanhq
import time
def get_dhan_client():
    client_id = os.getenv("CLIENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")

    if not client_id or not access_token:
        raise Exception("Dhan ENV variables not set")

    return dhanhq(client_id, access_token)
