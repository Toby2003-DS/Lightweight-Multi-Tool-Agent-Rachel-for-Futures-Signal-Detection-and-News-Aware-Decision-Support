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


@app.post("/api/chat/mcp")
async def chat_mcp(req: ChatRequest):
    """MCP-based chat endpoint - uses Claude API with MCP tool servers directly"""
    import anthropic
    import asyncio
    import subprocess
    import json as _json
    from pathlib import Path

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        dotenv_path = Path.home() / "zeroclaw" / ".env"
        if dotenv_path.exists():
            for line in dotenv_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip()

    async def call_mcp_tool(server_script, tool_name, arguments):
        messages = [
            _json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "rachel", "version": "1.0"}}}) + "\n",
            _json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}) + "\n",
            _json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool_name, "arguments": arguments}}) + "\n",
        ]
        proc = await asyncio.create_subprocess_exec(
            "python3", server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, _ = await asyncio.wait_for(
                proc.communicate(input="".join(messages).encode()),
                timeout=300
            )
        except asyncio.TimeoutError:
            proc.kill()
            return "Timeout"
        for line in stdout.decode().strip().split("\n"):
            if line.strip():
                try:
                    data = _json.loads(line)
                    if "result" in data and "content" in data["result"]:
                        return data["result"]["content"][0]["text"]
                except:
                    pass
        return "No result"

    workspace = str(Path.home() / "zeroclaw" / "scripts")
    signal_result = await call_mcp_tool(
        f"{workspace}/trading_signal_server.py",
        "get_trading_signals",
        {"symbol": "GC=F"}
    )
    news_result = await call_mcp_tool(
        f"{workspace}/news_pipeline_server.py",
        "get_news_sentiment",
        {"symbol": "Gold", "limit": 3}
    )

    client = anthropic.Anthropic(api_key=api_key)
    synthesis = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""You are Rachel, an AI futures trading assistant.

User question: {req.message}

Technical signals (from MCP trading_signal server):
{signal_result}

News sentiment (from MCP news_pipeline server):
{news_result}

Based on both sources, provide a comprehensive trading analysis and recommendation."""
        }]
    )
    return {"response": synthesis.content[0].text, "mode": "mcp"}
