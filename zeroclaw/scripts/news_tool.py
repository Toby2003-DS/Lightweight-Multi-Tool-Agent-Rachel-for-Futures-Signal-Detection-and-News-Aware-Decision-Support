#!/usr/bin/env python3
import argparse
import finnhub
import re
import os
from datetime import datetime

SYMBOL_MAP = {
    "黄金": ["gold", "precious metal", "XAU"],
    "Gold": ["gold", "precious metal", "XAU"],
    "原油": ["crude oil", "WTI", "OPEC", "petroleum"],
    "Crude Oil": ["crude oil", "WTI", "OPEC", "petroleum"],
    "白银": ["silver", "XAG"],
    "Silver": ["silver", "XAG"],
    "天然气": ["natural gas", "LNG"],
    "Natural Gas": ["natural gas", "LNG"],
    "纳指": ["nasdaq", "tech stocks", "NQ"],
    "Nasdaq": ["nasdaq", "tech stocks", "NQ"],
    "标普": ["S&P", "S&P 500", "SPX"],
    "S&P 500": ["S&P", "S&P 500", "SPX"],
}

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", default="Gold")
parser.add_argument("--limit", type=int, default=10)
parser.add_argument("--api_key", default=None)
args = parser.parse_args()

api_key = args.api_key or os.environ.get("FINNHUB_API_KEY")
if not api_key:
    print("Error: No Finnhub API key found. Set FINNHUB_API_KEY env variable.")
    exit(1)

keywords = SYMBOL_MAP.get(args.symbol, [args.symbol.lower()])
client = finnhub.Client(api_key=api_key)

all_news = []
for category in ["general", "forex"]:
    try:
        news = client.general_news(category, min_id=0)
        all_news.extend(news)
    except:
        pass

seen = set()
unique_news = []
for article in all_news:
    aid = article.get('id', article.get('headline', ''))
    if aid not in seen:
        seen.add(aid)
        unique_news.append(article)

results = []
for article in unique_news:
    text = (article.get('headline','') + ' ' + article.get('summary','')).lower()
    if any(kw.lower() in text for kw in keywords):
        results.append(article)
    if len(results) >= args.limit:
        break

if not results:
    results = unique_news[:args.limit]

results.sort(key=lambda x: x.get('datetime', 0), reverse=True)

print(f"Latest news for {args.symbol}:")
for i, article in enumerate(results, 1):
    dt = datetime.fromtimestamp(article.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')
    raw_summary = article.get('summary', 'N/A')
    clean_summary = re.sub(r'<[^>]+>', '', raw_summary).strip()[:300]
    print(f"\n[{i}] {dt}")
    print(f"Title: {article.get('headline', 'N/A')}")
    print(f"Summary: {clean_summary}")
    print(f"Source: {article.get('source', 'N/A')}")
