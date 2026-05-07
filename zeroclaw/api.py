from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import json
import re
import os
from pathlib import Path

HOME = Path.home()
WORKSPACE = HOME / ".zeroclaw" / "workspace"
ZEROCLAW_BIN = HOME / "zeroclaw" / "target" / "release" / "zeroclaw"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
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
        [str(ZEROCLAW_BIN), "agent", "-m", req.message],
        capture_output=True, text=True, timeout=120
    )
    response = clean_output(result.stdout)
    if not response:
        response = "Sorry, I could not process your request."
    return {"response": response}

@app.get("/api/kline")
async def kline(symbol: str = "GC=F", period: str = "1d", interval: str = "15m"):
    result = subprocess.run(
        ["python3", str(WORKSPACE / "kline.py"),
         "--symbol", symbol, "--period", period, "--interval", interval],
        capture_output=True, text=True, timeout=30
    )
    try:
        return json.loads(result.stdout.strip())
    except Exception:
        return []


@app.get("/api/news")
async def news(symbol: str = "Gold", limit: int = 5):
    env = dict(os.environ)
    env["FINNHUB_API_KEY"] = env.get("FINNHUB_API_KEY", "")
    result = subprocess.run(
        ["python3", str(WORKSPACE / "news_pipeline.py"),
         "--symbol", symbol, "--limit", str(limit), "--json"],
        capture_output=True, text=True, timeout=180, env=env
    )
    try:
        return json.loads(result.stdout.strip())
    except Exception:
        return {"symbol": symbol, "overall": "NEUTRAL", "score": 0, "total": 0, "articles": []}
