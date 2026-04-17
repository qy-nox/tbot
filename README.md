# 🚀 TBOT - Advanced Cryptocurrency Trading Signal Bot

## Features
- 📊 Real-time Binance price data
- 📈 ML-powered trading signals
- 💳 Subscription management
- 🤖 Telegram bots (Main + Subscription)
- 🔐 Advanced admin dashboard
- 📉 Performance tracking
- 🎯 Multi-timeframe analysis

## Installation
```bash
git clone https://github.com/qy-nox/tbot.git
cd tbot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## Usage
- 📱 Telegram Bot: @YourBotName
- 🌐 Dashboard: http://localhost:8000/dashboard/
- 🔐 Admin: http://localhost:8000/admin/
- 📚 API: http://localhost:8000/docs

## Configuration
Edit `.env` with your settings:
```env
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
TELEGRAM_BOT_TOKEN_MAIN=your_token
TELEGRAM_BOT_TOKEN_SUB=your_token
```

## Commands
- /start - Start bot
- /market - Live prices
- /signals - Active signals
- /performance - Statistics
- /help - Help menu
