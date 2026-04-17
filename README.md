# 🚀 TBOT - Advanced Crypto Trading Signal Bot

## Features
- Price action analysis
- 20+ technical indicators
- Multi-confirmation signal system
- Backtesting support
- Risk management (position sizing and limits)
- Economic calendar integration
- News sentiment analysis
- LSTM + XGBoost-capable ML stack
- Weekly performance tracking
- Real-time Telegram/Discord alerts

## Installation
1. Clone repo
2. Install dependencies: `pip install -r requirements.txt`
3. Copy env file: `cp .env.example .env`
4. Configure API keys
5. Run bot: `python main.py`

## Architecture
- Scanner: real-time pair scanning
- Strategy: multi-confirmation engine
- Risk: position sizing and trade limits
- Notifier: Telegram/Discord/email delivery

## API Endpoints
- `GET /signals` - Get active signals
- `POST /backtest` - Run backtest
- `GET /performance` - Performance metrics
- `GET /health` - System health

## Trading Pairs
BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, ADA/USDT

## Accuracy
- Backtested: 60-70%
- Live: 50-60% (with slippage)

## Support
GitHub Issues: https://github.com/qy-nox/tbot/issues
