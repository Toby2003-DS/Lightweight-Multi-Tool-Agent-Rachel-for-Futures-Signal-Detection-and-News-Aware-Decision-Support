#!/usr/bin/env python3
import sys
sys.path.insert(0, '/Users/zhangjiahao/TradingPatternScanner')

import argparse
import warnings
warnings.filterwarnings('ignore')

import yfinance as yf
from tradingpatterns import tradingpatterns

FUTURES_MAP = {
    "黄金": "GC=F", "原油": "CL=F", "白银": "SI=F",
    "天然气": "NG=F", "铜": "HG=F", "纳指": "NQ=F", "标普": "ES=F",
}

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", default="黄金")
parser.add_argument("--interval", default="15m")
parser.add_argument("--period", default="5d")
args = parser.parse_args()

ticker = FUTURES_MAP.get(args.symbol, args.symbol)
df = yf.download(ticker, period=args.period, interval=args.interval, progress=False)
df = df[['Open','High','Low','Close','Volume']].copy()
df.columns = ['Open','High','Low','Close','Volume']

df = tradingpatterns.detect_head_shoulder(df)
df = tradingpatterns.detect_multiple_tops_bottoms(df)
df = tradingpatterns.detect_triangle_pattern(df)
df = tradingpatterns.detect_wedge(df)
df = tradingpatterns.detect_channel(df)
df = tradingpatterns.detect_double_top_bottom(df)

pattern_cols = [c for c in df.columns if 'pattern' in c]
recent = df.tail(20)
results = []
for col in pattern_cols:
    signals = recent[recent[col].notna()]
    for ts, row in signals.iterrows():
        results.append(f"{ts.strftime('%H:%M')} | {row[col]} | 收盘价: {row['Close']:.2f}")

if not results:
    print(f"{args.symbol}（{ticker}）未检测到明显交易形态。")
else:
    print(f"{args.symbol}（{ticker}）检测到以下信号：")
    for r in results[-10:]:
        print(r)
