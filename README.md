# Lightweight Multi-Tool Agent for Futures Signal Detection and News-Aware Decision Support

**NYU - Advanced Topics in Data Science**

**Team:** Jiahao Zhang (Agent, Workflow, Fine-tune) · Jess Liang (Trading Signal Model) · Nicole (Data Preparation)

## Overview

Rachel is a lightweight AI agent that combines technical pattern detection and real-time news analysis to support futures trading decisions. The system integrates two specialized tools:

- Tool 1 - Technical Signal Detection: Identifies classic chart patterns (Head and Shoulder, Double Top/Bottom, Channel Up/Down, Wedge, Triangle) on futures price data using 15-minute OHLCV candles.
- Tool 2 - News Retrieval and Sentiment: Retrieves real-time financial news and performs sentiment scoring to support directional decision-making.

## System Architecture

zeroclaw Agent + Claude API
- Tool 1: TradingPatternScanner (technical signals)
- Tool 2: Web Search (news retrieval)
- FastAPI Backend + React UI

## Repository Structure

- zeroclaw/               Agent framework (Rust). Our custom files are in zeroclaw/scripts/ and zeroclaw/skills/
- TradingPatternScanner/  Pattern detection library
- trading-ui/             React frontend
- open-skills/            zeroclaw open skills
- api.py                  FastAPI backend (our code, in repo root)
- trading_signal.py       Trading signal detection script (our code, in repo root)

## Setup and Reproduction

All commands below assume you start from the repo root unless told otherwise.
After cloning: cd Lightweight-Multi-Tool-Agent-Rachel-for-Futures-Signal-Detection-and-News-Aware-Decision-Support

Prerequisites: macOS or Linux, Python 3.11+, Node.js 20+, Rust, Anthropic API key

Step 1 - Install Rust (skip if already installed):
curl --proto =https --tlsv1.2 -sSf https://sh.rustup.rs | sh
source /Users/zhangjiahao/.cargo/env

Step 2 - Build zeroclaw (from repo root):
cd zeroclaw
cargo build --release
cd ..

Step 3 - Configure API Key (from repo root):
Copy zeroclaw/.env.example to zeroclaw/.env
Edit zeroclaw/.env and add:
ANTHROPIC_API_KEY=sk-ant-your-key-here
PROVIDER=anthropic
ZEROCLAW_MODEL=claude-sonnet-4-6

Step 4 - Initialize zeroclaw Agent (from repo root):
cd zeroclaw
./target/release/zeroclaw onboard
When prompted: select Anthropic as provider, paste your API key, choose defaults for everything else.
cd ..

Step 5 - Install Python Dependencies (from repo root):
pip install fastapi uvicorn yfinance tradingpattern langchain-core langchain-anthropic

Step 6 - Install Trading Signal Skill (from repo root):
cp trading_signal.py ~/.zeroclaw/workspace/trading_signal.py
cd zeroclaw
./target/release/zeroclaw skills install skills/trading_signal
cd ..

Step 7 - Configure zeroclaw Settings:
Edit ~/.zeroclaw/config.toml and make the following changes:

Change these values:
max_context_tokens = 4000
max_history_messages = 3
auto_save = false
auto_hydrate = false
open_skills_enabled = false
allow_scripts = true

Find the auto_approve list and add shell to it:
auto_approve = [
    shell,
    file_read,
    ...
]

Step 8 - Install Frontend Dependencies (from repo root):
cd trading-ui
npm install
cd ..

Step 9 - Start the System (from repo root, open two terminals):
Terminal 1 - Backend:
uvicorn api:app --host 0.0.0.0 --port 8000

Terminal 2 - Frontend:
cd trading-ui
npm start

Step 10 - Open Browser:
http://localhost:3000

## Usage

1. Select a futures symbol from the left panel (Gold, Crude Oil, Silver, etc.)
2. The candlestick chart loads real-time 15-minute data via yfinance
3. Ask Rachel in the chat box, for example:
   - Analyze gold futures - give me technical signals and latest news
   - Should I go long or short on crude oil right now?
   - What are the key support and resistance levels for natural gas?

## Fine-tuning Plan (In Progress)

Fine-tune 1 - News Summarization LLM:
Train a small model (Qwen2.5-7B or LLaMA-3.1-8B) to summarize financial news and assign sentiment scores.
Dataset: EDGAR-CORPUS + synthetic data via Claude API distillation (target: 10,000 samples).

Fine-tune 2 - Agent LLM:
Replace the Claude API backbone with a fine-tuned small model trained on workflow trajectories.
Training approach: knowledge distillation from Claude (teacher) to small model (student).

## References

- zeroclaw (Agent framework): https://github.com/zeroclaw-labs/zeroclaw
- TradingPatternScanner (Pattern detection): https://github.com/white07S/TradingPatternScanner
- open-skills: https://github.com/zeroclaw-labs/open-skills
- EDGAR-CORPUS (Fine-tuning dataset): https://huggingface.co/datasets/eloukas/edgar-corpus

## License

This project is for academic use only (NYU Advanced Topics in Data Science).
Third-party components retain their original licenses.
