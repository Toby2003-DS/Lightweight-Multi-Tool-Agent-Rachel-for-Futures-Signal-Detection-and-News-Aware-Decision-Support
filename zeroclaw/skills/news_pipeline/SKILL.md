---
name: news_pipeline
description: Complete news pipeline - fetch latest financial news from Finnhub and analyze sentiment using fine-tuned Qwen2.5-7B model in one step
metadata: {"zeroclaw":{"emoji":"📊","requires":{"bins":["python3"]}}}
---

# News Pipeline Skill

One-step skill that fetches financial news AND analyzes sentiment using the fine-tuned Qwen2.5-7B model.

## Usage

```bash
python3 ~/.zeroclaw/workspace/news_pipeline.py --symbol Gold --limit 5
```

## Supported Symbols
Gold, Crude Oil, Silver, Natural Gas, Nasdaq, S&P 500 (and ticker codes: GC=F, CL=F, SI=F, NG=F, NQ=F, ES=F)

## Parameters
- --symbol: Futures symbol name (default: Gold)
- --limit: Number of articles to analyze (default: 5)

## Output Format
For each article:
- Timestamp and Source
- Title
- Analysis summary (1-2 sentences from fine-tuned model)
- Sentiment: Positive/Neutral/Negative with score (+1/0/-1)

Final output:
- Total articles analyzed
- Total sentiment score
- Overall: BULLISH / BEARISH / NEUTRAL

## IMPORTANT - When presenting results to user:
Always list EVERY article individually with:
1. The article title
2. The 1-2 sentence summary/analysis
3. The sentiment label and score

Do NOT summarize or compress the articles. Show each one explicitly.

## When to use this skill
Use when user asks about:
- News sentiment for a futures symbol
- Whether news is bullish or bearish
- Combined news analysis for trading decisions

After running this skill, combine the Overall sentiment with trading_signal output for a complete recommendation.
