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
