#!/usr/bin/env python3
import argparse
import finnhub
import re
import os
import sys
import json
import torch
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

SYMBOL_MAP = {
    "黄金": ["gold", "precious metal", "XAU", "bullion", "safe haven", "fed rate", "dollar"],
    "Gold": ["gold", "precious metal", "XAU", "bullion", "safe haven", "fed rate", "dollar"],
    "gold": ["gold", "precious metal", "XAU", "bullion", "safe haven", "fed rate", "dollar"],
    "GC": ["gold", "precious metal", "XAU", "bullion", "safe haven", "fed rate", "dollar"],
    "GC=F": ["gold", "precious metal", "XAU", "bullion", "safe haven", "fed rate", "dollar"],
    "XAUUSD": ["gold", "precious metal", "XAU", "bullion", "safe haven", "fed rate", "dollar"],
    "原油": ["crude oil", "WTI", "OPEC", "petroleum", "oil price", "barrel", "brent", "energy", "refinery"],
    "Crude Oil": ["crude oil", "WTI", "OPEC", "petroleum", "oil price", "barrel", "brent", "energy", "refinery"],
    "crude oil": ["crude oil", "WTI", "OPEC", "petroleum", "oil price", "barrel", "brent", "energy", "refinery"],
    "CL": ["crude oil", "WTI", "OPEC", "petroleum", "oil price", "barrel", "brent", "energy", "refinery"],
    "CL=F": ["crude oil", "WTI", "OPEC", "petroleum", "oil price", "barrel", "brent", "energy", "refinery"],
    "WTI": ["crude oil", "WTI", "OPEC", "petroleum", "oil price", "barrel", "brent", "energy", "refinery"],
    "白银": ["silver", "XAG"],
    "Silver": ["silver", "XAG"],
    "silver": ["silver", "XAG"],
    "SI": ["silver", "XAG"],
    "SI=F": ["silver", "XAG"],
    "XAGUSD": ["silver", "XAG"],
    "天然气": ["natural gas", "LNG"],
    "Natural Gas": ["natural gas", "LNG"],
    "natural gas": ["natural gas", "LNG"],
    "NG": ["natural gas", "LNG"],
    "NG=F": ["natural gas", "LNG"],
    "纳指": ["nasdaq", "tech stocks", "NQ"],
    "Nasdaq": ["nasdaq", "tech stocks", "NQ"],
    "nasdaq": ["nasdaq", "tech stocks", "NQ"],
    "NQ": ["nasdaq", "tech stocks", "NQ"],
    "NQ=F": ["nasdaq", "tech stocks", "NQ"],
    "标普": ["S&P", "S&P 500", "SPX"],
    "S&P 500": ["S&P", "S&P 500", "SPX"],
    "S&P": ["S&P", "S&P 500", "SPX"],
    "ES": ["S&P", "S&P 500", "SPX"],
    "ES=F": ["S&P", "S&P 500", "SPX"],
    "SPX": ["S&P", "S&P 500", "SPX"],
}

BASE_MODEL = "Qwen/Qwen2.5-7B-Instruct"
ADAPTER = "Jessliang/rachel-finetuned"

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", default="Gold")
parser.add_argument("--limit", type=int, default=5)
parser.add_argument("--json", action="store_true", dest="json_output", help="Output JSON instead of human-readable text")
args = parser.parse_args()

api_key = os.environ.get("FINNHUB_API_KEY")
if not api_key:
    if args.json_output:
        print(json.dumps({"error": "FINNHUB_API_KEY not set"}))
    else:
        print("Error: FINNHUB_API_KEY not set")
    exit(1)

# Step 1: Fetch news
print(f"Fetching news for {args.symbol}...", file=sys.stderr)
keywords = SYMBOL_MAP.get(args.symbol, [args.symbol.lower()])
client = finnhub.Client(api_key=api_key)

all_news = []
for category in ["general", "forex"]:
    try:
        all_news.extend(client.general_news(category, min_id=0))
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
    text = (article.get('headline', '') + ' ' + article.get('summary', '')).lower()
    if any(kw.lower() in text for kw in keywords):
        results.append(article)
    if len(results) >= args.limit:
        break

if not results:
    results = unique_news[:args.limit]

results.sort(key=lambda x: x.get('datetime', 0), reverse=True)

# Step 2: Load model
print("Loading sentiment model...", file=sys.stderr)
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, dtype=torch.float16, device_map={"": "mps"})
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()
print("Model ready.", file=sys.stderr)

def analyze(text):
    messages = [
        {"role": "system", "content": "Summarize the following financial news article in 1-2 sentences. Then classify the sentiment as Positive, Neutral, or Negative."},
        {"role": "user", "content": text}
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to("mps")
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=150, do_sample=False)
    result = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    sentiment = "Neutral"
    r = result.lower()
    if any(x in r for x in ["sentiment: positive", "sentiment is positive", "positive sentiment", "is positive"]):
        sentiment = "Positive"
    elif any(x in r for x in ["sentiment: negative", "sentiment is negative", "negative sentiment", "is negative", "negative towards"]):
        sentiment = "Negative"
    return result.strip(), sentiment

# Step 3: Analyze each article
scores = {"Positive": 1, "Neutral": 0, "Negative": -1}
total = 0
articles = []

for i, article in enumerate(results, 1):
    dt = datetime.fromtimestamp(article.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')
    title = article.get('headline', 'N/A')
    source = article.get('source', '')
    url = article.get('url', '')
    raw_summary = article.get('summary', '')
    clean_summary = re.sub(r'<[^>]+>', '', raw_summary).strip()[:500]
    input_text = f"Title: {title}\nSummary: {clean_summary}"
    analysis, sentiment = analyze(input_text)
    score = scores[sentiment]
    total += score

    # Strip trailing sentiment sentence for cleaner summary
    summary = analysis
    for marker in ["The sentiment", "Sentiment:", "This sentiment"]:
        if marker in summary:
            summary = summary[:summary.index(marker)].strip()
    if summary.startswith("Summary:"):
        summary = summary.replace("Summary:", "").strip()

    articles.append({
        "rank": i,
        "datetime": dt,
        "source": source,
        "title": title,
        "url": url,
        "summary": summary,
        "sentiment": sentiment,
        "score": score,
    })

if total > 0:
    overall = "BULLISH"
elif total < 0:
    overall = "BEARISH"
else:
    overall = "NEUTRAL"

if args.json_output:
    print(json.dumps({
        "symbol": args.symbol,
        "overall": overall,
        "score": total,
        "total": len(articles),
        "articles": articles,
    }))
else:
    print(f"\n=== News Sentiment Analysis for {args.symbol} ===")
    for a in articles:
        print(f"\n[{a['rank']}] {a['datetime']} | {a['source']}")
        print(f"Title: {a['title']}")
        print(f"URL: {a['url']}")
        print(f"Analysis: {a['summary']}")
        print(f"Sentiment: {a['sentiment']} ({'+' if a['score'] > 0 else ''}{a['score']})")
    print(f"\n{'='*40}")
    print(f"Articles analyzed: {len(articles)}")
    print(f"Total Sentiment Score: {total}/{len(articles)}")
    print(f"Overall News Sentiment: {overall}")
