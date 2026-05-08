#!/usr/bin/env python3
"""MCP Server for Trading Signal Detection"""

import subprocess
import sys
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

app = Server("trading-signal-server")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_trading_signals",
            description="Detect technical chart patterns for a futures symbol using TradingPatternScanner. Returns detected patterns including Head and Shoulders, Double Top/Bottom, Channel, Wedge, and Triangle formations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Futures ticker symbol (e.g. GC=F for Gold, CL=F for Crude Oil, SI=F for Silver, NG=F for Natural Gas, NQ=F for Nasdaq, ES=F for S&P 500)"
                    },
                    "interval": {
                        "type": "string",
                        "description": "Time interval for OHLCV data",
                        "default": "15m"
                    }
                },
                "required": ["symbol"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "get_trading_signals":
        raise ValueError(f"Unknown tool: {name}")

    symbol = arguments.get("symbol", "GC=F")
    interval = arguments.get("interval", "15m")
    script_path = Path.home() / ".zeroclaw" / "workspace" / "trading_signal.py"

    result = subprocess.run(
        ["python3", str(script_path), "--symbol", symbol, "--interval", interval],
        capture_output=True, text=True, timeout=60
    )

    output = result.stdout.strip() if result.stdout else "No patterns detected."
    if result.returncode != 0 and result.stderr:
        output = f"Error: {result.stderr.strip()}"

    return [types.TextContent(type="text", text=output)]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
