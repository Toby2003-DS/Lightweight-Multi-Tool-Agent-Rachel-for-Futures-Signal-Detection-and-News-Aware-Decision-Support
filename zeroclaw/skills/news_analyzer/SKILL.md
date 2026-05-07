---
name: news_analyzer
description: Analyze financial news sentiment using fine-tuned Qwen2.5-7B model (Jessliang/rachel-finetuned)
metadata: {"zeroclaw":{"emoji":"🧠","requires":{"bins":["python3"]}}}
---

# News Analyzer Skill

Analyze financial news articles using a fine-tuned LLM to generate summaries and sentiment scores.

## Usage

Always pass both --titles and --news together:

```bash
python3 ~/.zeroclaw/workspace/news_analyzer.py   --titles "Title of article 1" "Title of article 2" "Title of article 3"   --news "Summary text of article 1" "Summary text of article 2" "Summary text of article 3"
```

## Output Format
For each article:
- [N] Article Title
- Summary (1-2 sentences from model)
- Sentiment: Positive/Neutral/Negative (+1/0/-1)

Final output:
- Total sentiment score (e.g. 2/5)
- Overall: BULLISH / BEARISH / NEUTRAL

## When to use this skill
1. First use news_search skill to get latest news for a symbol
2. Pass the article titles to --titles and article summaries to --news
3. Combine the Overall sentiment score with trading_signal output for final recommendation
