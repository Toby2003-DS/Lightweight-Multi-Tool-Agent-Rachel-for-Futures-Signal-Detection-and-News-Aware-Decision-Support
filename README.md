# Lightweight Multi-Tool Agent for Futures Signal Detection and News-Aware Decision Support

**NYU - Advanced Topics in Data Science**

**Team:** Jiahao Zhang (Agent, Workflow, Fine-tune) · Jess Liang (Trading Signal Model) · Nicole (Data Preparation)

## Overview

Rachel is a lightweight AI agent that combines technical pattern detection and real-time news analysis to support futures trading decisions. The system integrates two specialized tools:

- **Tool 1 - Technical Signal Detection:** Identifies classic chart patterns (Head and Shoulder, Double Top/Bottom, Channel Up/Down, Wedge, Triangle) on futures price data using 15-minute OHLCV candles.
- **Tool 2 - News Retrieval and Sentiment:** Retrieves real-time financial news and performs sentiment scoring to support directional decision-making.

## System Architecture

zeroclaw Agent + Claude API
- Tool 1: TradingPatternScanner (technical signals)
- Tool 2: Web Search (news retrieval)
- FastAPI Backend + React UI

## Repository Structure

- zeroclaw/ - Agent framework, our scripts and skills are in scripts/ and skills/
- TradingPatternScanner/ - Pattern detection library
- trading-ui/ - React frontend
- open-skills/ - zeroclaw open skills
- api.py - FastAPI backend (our code)

## Setup and Reproduction

Prerequisites: macOS or Linux, Python 3.11+, Node.js 20+, Rust, Anthropic API key

Step 1 - Install Rust:
curl --proto =https --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

Step 2 - Build zeroclaw:
cd zeroclaw
cargo build --release

Step 3 - Configure API Key:
Copy zeroclaw/.env.example to zeroclaw/.env
Add: ANTHROPIC_API_KEY=your-key, PROVIDER=anthropic, ZEROCLAW_MODEL=claude-sonnet-4-6

Step 4 - Initialize zeroclaw Agent:
cd zeroclaw
./target/release/zeroclaw onboard
Select Anthropic as provider, paste your API key, choose defaults for everything else.

Step 5 - Install Python Dependencies:
pip install fastapi uvicorn yfinance tradingpattern langchain-core langchain-anthropic

Step 6 - Install Trading Signal Skill:
cp trading_signal.py ~/.zeroclaw/workspace/trading_signal.py
cd zeroclaw
./target/release/zeroclaw skills install skills/trading_signal

Step 7 - Configure zeroclaw Settings:
Edit ~/.zeroclaw/config.toml and set:
max_context_tokens = 4000
max_history_messages = 3
auto_save = false
auto_hydrate = false
open_skills_enabled = false
allow_scripts = true
Also add shell to the auto_approve list.

Step 8 - Install Frontend Dependencies:
cd trading-ui
npm install

Step 9 - Start the System:
Terminal 1 (Backend): cd repo-root && uvicorn api:app --host 0.0.0.0 --port 8000
Terminal 2 (Frontend): cd trading-ui && npm start

Step 10 - Open Browser: http://localhost:3000

## Usage

1. Select a futures symbol from the left panel (Gold, Crude Oil, Silver, etc.)
2. The candlestick chart loads real-time 15-minute data via yfinance
3. Ask Rachel in the chat box, for example:
   - Analyze gold futures - give me technical signals and latest news
   - Should I go long or short on crude oil right now?

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
