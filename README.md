# Rachel — AI Futures Trading Assistant

A lightweight multi-tool AI agent for futures signal detection and news-aware trading decision support.

## Architecture

zeroclaw (Agent) + Claude API
- Tool 1: TradingPatternScanner (technical signals)
- Tool 2: Web Search (news retrieval)
- FastAPI backend + React UI

## Setup

### 1. Install Dependencies
pip install fastapi uvicorn yfinance tradingpattern langchain-core langchain-anthropic

### 2. Install zeroclaw
git clone https://github.com/zeroclaw-labs/zeroclaw.git
cd zeroclaw
cargo build --release
./target/release/zeroclaw onboard

### 3. Configure API Key
Add your Anthropic API key to .env file

### 4. Install Trading Skill
cp trading_signal.py ~/.zeroclaw/workspace/
./zeroclaw/target/release/zeroclaw skills install skills/trading_signal

### 5. Start the System
Terminal 1 - Backend: uvicorn api:app --host 0.0.0.0 --port 8000
Terminal 2 - Frontend: cd trading-ui && npm start

### 6. Open Browser
http://localhost:3000

## Team
- Jiahao Zhang: Agent, workflow, fine-tune
- Jess Liang: Trading signal model
- Nicole: Data preparation
