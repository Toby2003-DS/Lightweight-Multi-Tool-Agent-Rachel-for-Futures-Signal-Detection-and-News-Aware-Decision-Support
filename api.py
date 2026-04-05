from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

def clean_output(text):
    lines = text.strip().split("\n")
    clean = []
    skip_keywords = ["INFO ", "WARN ", "ERROR ", "DEBUG ", "Config loaded",
                     "Memory init", "sandbox", "[2m", "[32m", "[0m", "zeroclaw::"]
    for line in lines:
        if any(kw in line for kw in skip_keywords):
            continue
        line = re.sub(r'\x1b\[[0-9;]*m', '', line)
        if line.strip():
            clean.append(line)
    return "\n".join(clean).strip()

@app.post("/api/chat")
async def chat(req: ChatRequest):
    result = subprocess.run(
        ["/Users/zhangjiahao/zeroclaw/target/release/zeroclaw", "agent", "-m", req.message],
        capture_output=True, text=True, timeout=120
    )
    response = clean_output(result.stdout)
    if not response:
        response = "Sorry, I could not process your request."
    return {"response": response}

@app.get("/api/kline")
async def kline(symbol: str = "GC=F"):
    result = subprocess.run(
        ["python3", "-c", f"""
import yfinance as yf, json
df = yf.download("{symbol}", period="1d", interval="15m", progress=False)
df = df[['Open','High','Low','Close']].dropna()
data = []
for ts, row in df.iterrows():
    data.append({{"time": int(ts.timestamp()), "open": round(float(row['Open']),2), "high": round(float(row['High']),2), "low": round(float(row['Low']),2), "close": round(float(row['Close']),2)}})
print(json.dumps(data))
"""],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout.strip())
    except:
        return []
