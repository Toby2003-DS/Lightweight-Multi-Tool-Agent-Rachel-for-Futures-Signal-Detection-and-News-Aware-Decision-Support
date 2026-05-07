---
name: news_search
description: Search latest financial news for futures symbols using Finnhub API
metadata: {"zeroclaw":{"emoji":"📰","requires":{"bins":["python3"]}}}
---

# News Search Skill

Search real-time financial news for futures symbols from Finnhub.

## Supported Symbols
Gold, Crude Oil, Silver, Natural Gas, Nasdaq, S&P 500 (and Chinese names: 黄金, 原油, 白银, 天然气, 纳指, 标普)

## Usage

### Search news for a symbol
```bash
python3 ~/.zeroclaw/workspace/news_tool.py --symbol Gold --api_key $FINNHUB_API_KEY --limit 5
```

## Parameters
- --symbol: Symbol name (Gold/Crude Oil/Silver/Natural Gas/Nasdaq/S&P 500)
- --limit: Number of articles to return (default: 5)
- --api_key: Finnhub API key

## Output Format
Each article includes:
- Timestamp
- Title
- Summary (up to 300 chars)
- Source

## When to use this skill
Use when user asks about:
- Latest news for a futures symbol
- Market sentiment for a commodity
- Recent events affecting a futures price
- News-based trading recommendations
