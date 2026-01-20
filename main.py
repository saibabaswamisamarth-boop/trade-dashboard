from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from dhanhq import dhanhq
import os

from market_pulse_engine import process_stock
from stocks_master import FO_STOCKS
print("Total stocks loaded:", len(FO_STOCKS))

app = FastAPI()templates = Jinja2Templates(directory="templates")

# =========================
# MARKET PULSE V2 API
# =========================

@app.get("/market-pulse-v2")
def market_pulse_v2(batch: int = Query(1, ge=1)):

    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    current_batch = batches[batch - 1]

    for symbol, sid in current_batch:
        try:
            quote = dhan.quote_data(
                securities={"NSE_EQ": [sid]}
            )

            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse:
                continue

            data = nse[str(sid)]
            result = process_stock(symbol, data)
            results.append(result)

        except Exception as e:
            print(symbol, e)

    return {
        "batch": batch,
        "total_batches": len(batches),
        "data": results
    }

# =========================
# GLOBAL DATA (VERY IMPORTANT)
# =========================

FO_STOCKS_FULL = {
    "ADANIENT": 25,
    "ADANIPORTS": 15083,
    "APOLLOHOSP": 157,
    "ASIANPAINT": 236,
    "AXISBANK": 5900,
    "BAJFINANCE": 317,
    "RELIANCE": 2885,
    "SBIN": 3045,
    "TCS": 11536,
    "WIPRO": 3787
}

BATCH_SIZE = 15

def get_batches(stock_dict):
    items = list(stock_dict.items())
    return [items[i:i+BATCH_SIZE] for i in range(0, len(items), BATCH_SIZE)]

# =========================
# DHAN CLIENT
# =========================

def get_dhan_client():
    client_id = os.getenv("CLIENT_ID")
    access_token = os.getenv("ACCESS_TOKEN")

    if not client_id or not access_token:
        raise Exception("Dhan ENV variables not set")

    return dhanhq(client_id, access_token)

# =========================
# BASIC ROUTES
# =========================

@app.get("/health")
def health():
    return {"status": "ok"}

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

@from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "fo_dashboard.html",
        {"request": request}
    )


# =========================
# F&O LIVE SCAN
# =========================

@app.get("/fo-live-scan")
def fo_live_scan(batch: int = Query(1, ge=1)):

    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    total_batches = len(batches)

    if batch > total_batches:
        return {"batch": batch, "total_batches": total_batches, "data": []}

    current_batch = batches[batch - 1]

    for symbol, sid in current_batch:
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
            volume = data.get("volume", 0)
            avg_price = data.get("average_price", last_price)
            open_price = ohlc.get("open", last_price)

            score = 0
            if last_price > open_price:
                score += 1
            if last_price > avg_price:
                score += 1

            results.append({
                "symbol": symbol,
                "last_price": last_price,
                "volume": volume,
                "score": score
            })

        except Exception as e:
            print(f"{symbol} error:", e)

    return {
        "batch": batch,
        "total_batches": total_batches,
        "data": results
    }


# =========================
# DASHBOARD UI
# =========================

@app.get("/fo-dashboard", response_class=HTMLResponse)
def fo_dashboard(request: Request):
    return templates.TemplateResponse(
        "fo_dashboard.html",
        {"request": request}
    )


<script>
let batch = 1;
async function loadData(){
  const r = await fetch(`/market-pulse-v2?batch=${batch}`);
  const res = await r.json();
  const data = res.data;

  let rows = `
    <tr><th>Symbol</th><th>Price</th><th>Volume</th><th>Strength</th></tr>
  `;
  res.data.forEach(x=>{
    let badge = x.score==2 ? '<span class="green">STRONG</span>' :
                             '<span class="yellow">MEDIUM</span>';
    rows += `<tr>
      <td>${x.symbol}</td>
      <td>${x.last_price}</td>
      <td>${x.volume}</td>
      <td>${badge}</td>
    </tr>`;
  });
  document.getElementById("tbl").innerHTML = rows;
  batch++; if(batch>res.total_batches) batch=1;
}
loadData(); setInterval(loadData,10000);
</script>
</body>
</html>
"""
@app.get("/market-pulse-v2")
def market_pulse_v2(batch: int = Query(1, ge=1)):

    dhan = get_dhan_client()
    results = []

    batches = get_batches(FO_STOCKS_FULL)
    total_batches = len(batches)

    if batch > total_batches:
        return {"batch": batch, "total_batches": total_batches, "data": []}

    current_batch = batches[batch - 1]

    for symbol, sid in current_batch:
        try:
            quote = dhan.quote_data(
                securities={"NSE_EQ": [sid]}
            )

            nse = quote.get("data", {}).get("data", {}).get("NSE_EQ", {})
            if str(sid) not in nse:
                continue

            data = nse[str(sid)]

            # 🔥 ENGINE CALL (IMPORTANT)
            result = process_stock(symbol, data)
            results.append(result)

        except Exception as e:
            print(symbol, e)

    return {
        "batch": batch,
        "total_batches": total_batches,
        "data": results
    }
