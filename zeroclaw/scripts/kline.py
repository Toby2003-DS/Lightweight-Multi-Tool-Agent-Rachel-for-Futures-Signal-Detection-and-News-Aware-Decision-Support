#!/usr/bin/env python3
import argparse
import json
import yfinance as yf

parser = argparse.ArgumentParser()
parser.add_argument("--symbol", default="GC=F")
parser.add_argument("--period", default="1d")
parser.add_argument("--interval", default="15m")
args = parser.parse_args()

df = yf.download(args.symbol, period=args.period, interval=args.interval, progress=False)
df = df[['Open', 'High', 'Low', 'Close']].dropna()

data = []
for ts, row in df.iterrows():
    data.append({
        "time":  int(ts.timestamp()),
        "open":  round(float(row['Open']),  2),
        "high":  round(float(row['High']),  2),
        "low":   round(float(row['Low']),   2),
        "close": round(float(row['Close']), 2),
    })

print(json.dumps(data))
