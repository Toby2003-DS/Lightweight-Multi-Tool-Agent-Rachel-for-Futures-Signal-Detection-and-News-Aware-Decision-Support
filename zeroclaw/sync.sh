#!/bin/bash
# Sync scripts from zeroclaw/scripts/ to ~/.zeroclaw/workspace/
cp ~/zeroclaw/scripts/news_pipeline.py ~/.zeroclaw/workspace/news_pipeline.py
cp ~/zeroclaw/scripts/news_analyzer.py ~/.zeroclaw/workspace/news_analyzer.py
cp ~/zeroclaw/scripts/news_tool.py ~/.zeroclaw/workspace/news_tool.py
cp ~/zeroclaw/scripts/trading_signal.py ~/.zeroclaw/workspace/trading_signal.py
cp ~/zeroclaw/scripts/kline.py ~/.zeroclaw/workspace/kline.py
cp ~/zeroclaw/scripts/trading_signal_server.py ~/.zeroclaw/workspace/trading_signal_server.py
cp ~/zeroclaw/scripts/news_pipeline_server.py ~/.zeroclaw/workspace/news_pipeline_server.py
echo "Synced all scripts to workspace."
