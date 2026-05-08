#!/usr/bin/env python3
"""MCP Server for News Sentiment Pipeline"""

import subprocess
import sys
import os
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("news-pipeline-server")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_news_sentiment",
            description="Fetch latest financial news for a futures symbol from Finnhub and analyze sentiment using a fine-tuned Qwen2.5-7B model. Returns article summaries with Positive/Neutral/Negative sentiment labels and an overall BULLISH/BEARISH/NEUTRAL score.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Futures symbol name (e.g. Gold, Crude Oil, Silver, Natural Gas, Nasdaq, S&P 500)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of articles to retrieve and analyze",
                        "default": 5
                    }
                },
                "required": ["symbol"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "get_news_sentiment":
        raise ValueError(f"Unknown tool: {name}")

    symbol = arguments.get("symbol", "Gold")
    limit = arguments.get("limit", 5)
    script_path = Path.home() / ".zeroclaw" / "workspace" / "news_pipeline.py"

    env = dict(os.environ)
    finnhub_key = env.get("FINNHUB_API_KEY", "")
    if not finnhub_key:
        dotenv_path = Path.home() / "zeroclaw" / ".env"
        if dotenv_path.exists():
            for line in dotenv_path.read_text().splitlines():
                if line.startswith("FINNHUB_API_KEY="):
                    finnhub_key = line.split("=", 1)[1].strip()
                    env["FINNHUB_API_KEY"] = finnhub_key
                    break

    result = subprocess.run(
        ["python3", str(script_path), "--symbol", symbol, "--limit", str(limit)],
        capture_output=True, text=True, timeout=300, env=env
    )

    output = result.stdout.strip() if result.stdout else "No news retrieved."
    if result.returncode != 0 and result.stderr:
        output = f"Error: {result.stderr.strip()}"

    return [types.TextContent(type="text", text=output)]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
