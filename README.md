# Advanced Cryptocurrency Trading Signal Bot

A production-ready, modular cryptocurrency trading signal bot with technical analysis, sentiment analysis, risk management, backtesting, and Telegram notifications.

## Features

| Feature | Description |
|---------|-------------|
| **Data Fetching** | OHLCV, crypto news, economic calendar, funding rates, volume profiles via CCXT (200+ exchanges) |
| **Technical Analysis** | RSI, EMA (20/50/200), MACD, Bollinger Bands, ATR, ADX, Fibonacci, support/resistance |
| **Multi-Indicator Signals** | Consensus-based: at least 2 of 4 sub-strategies (RSI, MACD, EMA, Bollinger) must agree |
| **Advanced Filtering** | Trend, momentum, volatility, ADX strength, high-impact news avoidance |
| **Risk Management** | Auto position sizing, volatility-based SL, multiple TP levels, Kelly Criterion, max drawdown protection |
| **Backtesting** | Vectorized engine with Sharpe ratio, Sortino ratio, max drawdown, profit factor, per-trade logs |
| **Sentiment Analysis** | TextBlob + VADER with weighted aggregation and impact classification |
| **Telegram Notifications** | Real-time signal alerts, performance reports, error notifications |
| **Database** | SQLAlchemy ORM for signal, trade, and performance logging |
| **Production Ready** | Error handling, rotating file logs, environment-variable config, async-capable |

## Project Structure

```
tbot/
├── config/
│   ├── __init__.py
│   └── settings.py              # All configuration & trading parameters
├── core/
│   ├── __init__.py
│   ├── data_fetcher.py          # OHLCV, news, funding rates, volume profiles
│   ├── technical_analyzer.py    # RSI, EMA, MACD, BB, ATR, ADX, Fibonacci, S/R
│   └── sentiment_analyzer.py    # TextBlob + VADER sentiment
├── risk_management/
│   ├── __init__.py
│   └── position_sizer.py        # Position sizing, SL/TP, Kelly, drawdown
├── backtesting/
│   ├── __init__.py
│   └── backtest_engine.py       # Vectorized backtest with full metrics
├── strategies/
│   ├── __init__.py
│   └── strategy_engine.py       # Multi-indicator consensus + filters
├── notifications/
│   ├── __init__.py
│   └── telegram_notifier.py     # Telegram bot integration
├── utils/
│   ├── __init__.py
│   ├── database.py              # SQLAlchemy models & helpers
│   └── logger.py                # Rotating file + console logging
├── main.py                      # Entry point – bot loop
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variable template
├── .gitignore
└── README.md
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/qy-nox/tbot.git
cd tbot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

| Variable | Description |
|----------|-------------|
| `BINANCE_API_KEY` | Binance API key |
| `BINANCE_API_SECRET` | Binance API secret |
| `FINNHUB_API_KEY` | Finnhub API key (for news) |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `TRADING_MODE` | `paper` (default) or `live` |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### 5. Initialise the database

```bash
python -c "from utils.database import init_db; init_db()"
```

### 6. Run the bot

```bash
python main.py
```

## Signal Example

```
🚀 TRADING SIGNAL

Pair: BTC/USDT
Direction: BUY
Entry: $42,500.0000

Targets:
  TP1: $43,000.0000
  TP2: $43,500.0000
  TP3: $44,000.0000

Stop Loss: $42,000.0000
Confidence: 85%
Trend: UPTREND

Reason: RSI oversold (28.5); MACD bullish crossover; EMA bullish alignment (20>50>200)
```

## Backtesting

```python
from core.data_fetcher import DataFetcher
from backtesting.backtest_engine import BacktestEngine

fetcher = DataFetcher()
df = fetcher.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=1000)

engine = BacktestEngine()
result = engine.run(df)

print(f"Total Trades: {result.total_trades}")
print(f"Win Rate:     {result.win_rate:.1%}")
print(f"Total Return: {result.total_return_pct:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.1%}")
print(f"Profit Factor:{result.profit_factor:.2f}")
```

## Configuration

All parameters are centralised in `config/settings.py` and can be overridden via environment variables. Key settings:

- **Trading pairs** – default: BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, XRP/USDT, ADA/USDT
- **Timeframe** – default: 1h
- **Risk per trade** – default: 2 %
- **Max open trades** – default: 5
- **Max drawdown** – default: 10 %
- **Signal confidence threshold** – default: 60 %
- **Scan interval** – default: 300 s (5 min)

## Security Notes

- **Never** commit your `.env` file to version control.
- Use environment variables or a secrets manager for API keys.
- Always test with `TRADING_MODE=paper` before enabling live trading.
- Start with small position sizes and monitor performance.

## License

This project is provided as-is for educational and personal use. Use at your own risk. Cryptocurrency trading involves significant financial risk.
