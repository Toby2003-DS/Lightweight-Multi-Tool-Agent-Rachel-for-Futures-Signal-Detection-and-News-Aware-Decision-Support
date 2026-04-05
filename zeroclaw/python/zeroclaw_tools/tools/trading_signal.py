"""
Trading pattern detection tool using TradingPatternScanner + yfinance.
"""

import sys
sys.path.insert(0, '/Users/zhangjiahao/TradingPatternScanner')

import yfinance as yf
from tradingpatterns import tradingpatterns
from langchain_core.tools import tool

FUTURES_MAP = {
    "黄金": "GC=F",
    "原油": "CL=F",
    "白银": "SI=F",
    "天然气": "NG=F",
    "铜": "HG=F",
    "纳指": "NQ=F",
    "标普": "ES=F",
}

@tool
def detect_trading_patterns(symbol: str, interval: str = "15m", period: str = "5d") -> str:
    """
    检测期货品种的交易形态信号。
    symbol: 品种名称，如 '黄金', '原油'，或直接输入代码如 'GC=F'
    interval: 时间窗口，如 '15m', '1h', '1d'
    period: 回溯周期，如 '1d', '5d'
    """
    ticker = FUTURES_MAP.get(symbol, symbol)

    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return f"无法获取 {symbol} 的数据，请检查品种代码。"

        df = df[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        # 运行所有形态检测
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
            return f"{symbol}（{ticker}）在最近 {interval} 窗口内未检测到明显交易形态。"

        return f"{symbol}（{ticker}）检测到以下信号：\n" + "\n".join(results[-10:])

    except Exception as e:
        return f"检测出错: {str(e)}"
