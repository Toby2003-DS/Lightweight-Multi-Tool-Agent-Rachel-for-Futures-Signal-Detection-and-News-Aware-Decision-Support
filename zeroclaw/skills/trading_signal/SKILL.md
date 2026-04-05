---
name: trading_signal
description: 检测期货品种的交易形态信号，包括头肩顶、双顶双底、通道、楔形等
metadata: {"zeroclaw":{"emoji":"📈","requires":{"bins":["python3"]}}}
---

# Trading Signal Skill

## 使用方式

```bash
python3 /Users/zhangjiahao/.zeroclaw/workspace/trading_signal.py --symbol 黄金 --interval 15m
```

## 参数
- --symbol: 品种名称（黄金/原油/白银/天然气/铜/纳指/标普）
- --interval: 时间窗口（1m/5m/15m/1h/1d）
- --period: 回溯周期（1d/5d/1mo）
