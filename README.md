# Professional Trading Signal Service Platform

A production-ready SAAS platform for crypto and binary trading signal generation, distribution, and user management. Built on top of a modular trading bot with technical analysis, sentiment analysis, AI/ML prediction, on-chain analytics, multi-timeframe analysis, risk management, and backtesting.

## How the Full Ecosystem Works

The platform is designed as a **multi-bot ecosystem** with a unified backend:

1. **Subscription & Payment Flow (Bot 1 responsibilities)**
   - User onboarding and plan selection
   - Payment capture/verification workflow
   - Activation of subscription access after approval

2. **User/Admin Control Flow (Bot 2 responsibilities)**
   - Admin controls for users, plans, groups, notifications, and approvals
   - Renewal and expiry lifecycle management
   - Reporting and analytics orchestration

3. **Signal Validation/Distribution Flow (Bot 3 responsibilities)**
   - Signal intake from strategy engines
   - Grade/confidence filtering and anti-duplicate checks
   - Tier-aware formatting and channel distribution

4. **Admin Web/API + Mobile Clients**
   - FastAPI endpoints for auth, users, subscriptions, payments, signals, and analytics
   - Web dashboard for operational control and reporting
   - Mobile client support for subscriptions, signal history, and performance views

5. **Unified Data Layer**
   - Shared SQL models for users, subscriptions, payments, signals, deliveries, outcomes, and audit logs
   - Services use this data to enforce tiers, limits, and access rules consistently

## Profitability Disclaimer

- The system helps generate, score, and distribute trading signals with structured risk controls.
- **No signal platform can guarantee profits.**
- Real-world performance depends on market conditions, execution quality, slippage, and user risk management.
- Always paper-trade first and use strict position sizing.

## Platform Features

| Category | Features |
|----------|----------|
| **User Management** | Registration, JWT authentication, subscription tiers (Free / Premium / VIP), user profiles |
| **Signal Types** | Crypto trading signals (Binance, Bybit, etc.) and binary trading signals (CALL/PUT) |
| **Signal Quality** | Auto-grading (A+, A, B, C), confidence scoring, win-rate filtering, validity periods |
| **AI/ML Engine** | 7-model voting stack (LightGBM, XGBoost-proxy, RandomForest, Neural-Net-proxy, Isolation-Forest-proxy, GradientBoosting, SVM-proxy) with regime-aware meta voting |
| **Multi-Timeframe** | Simultaneous analysis with weighted consensus and confluence scoring |
| **On-Chain Data** | Whale tracking, exchange inflow/outflow, network metrics (free APIs) |
| **Distribution** | Telegram groups & channels, Discord webhooks, email, API — with retry on failure |
| **Performance** | Win rate (daily/weekly/monthly), ROI tracking, per-pair analytics, leaderboards |
| **Subscriptions** | Tiered plans with payment tracking, billing history, expiry management |
| **Web Dashboard** | Real-time signal dashboard, performance stats, mobile responsive |
| **Admin Dashboard** | User management, signal management, revenue tracking, performance snapshots |
| **Security** | JWT tokens, password hashing (bcrypt), audit logging, CORS |
| **Bot Engine** | RSI, EMA, MACD, Bollinger Bands, ATR, ADX, Fibonacci, supply/demand zones, order blocks |

## Project Structure

```
tbot/
├── config/
│   └── settings.py                  # Trading parameters, API config, ML/binary settings
├── core/
│   ├── data_fetcher.py              # OHLCV, news, funding rates
│   ├── technical_analyzer.py        # 10+ indicators, S/R, Fibonacci, supply/demand zones, order blocks
│   ├── sentiment_analyzer.py        # TextBlob + VADER sentiment
│   ├── multi_timeframe.py           # Multi-timeframe analysis (5m, 1h, 4h)
│   ├── onchain_analyzer.py          # Whale tracking & on-chain metrics
│   └── ml_engine.py                 # 3-model AI/ML ensemble (LightGBM, RF, GB)
├── strategies/
│   ├── strategy_engine.py           # Crypto multi-indicator consensus
│   └── binary_strategy.py           # Binary CALL/PUT signal generation
├── risk_management/
│   └── position_sizer.py            # Position sizing, SL/TP, Kelly
├── backtesting/
│   └── backtest_engine.py           # Vectorized backtesting
├── notifications/
│   └── telegram_notifier.py         # Telegram integration
├── utils/
│   ├── database.py                  # Original SQLAlchemy models
│   └── logger.py                    # Rotating file + console logging
├── signal_platform/                 # ── SAAS Platform ──
│   ├── models.py                    # Extended DB (users, subscriptions, payments, signals, deliveries, audit)
│   ├── auth.py                      # JWT authentication & password hashing
│   ├── schemas.py                   # Pydantic request/response schemas
│   ├── dashboard.py                 # Web dashboard (real-time stats)
│   ├── api/
│   │   └── app.py                   # FastAPI REST API (all routes)
│   └── services/
│       ├── user_service.py          # User registration, auth, profiles
│       ├── signal_service.py        # Signal creation, grading, quality
│       ├── subscription_service.py  # Plans, payments, billing
│       ├── distribution_service.py  # Multi-channel signal delivery
│       └── performance_service.py   # Analytics, win rates, leaderboards
├── main.py                          # Entry point (bot / API / both)
├── requirements.txt
├── .env.example
└── README.md
```

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/qy-nox/tbot.git
cd tbot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys, JWT_SECRET, etc.
```

### 3. Run

```bash
# Start the REST API server only
python main.py --api

# Start the trading bot scanner only
python main.py

# Start both (API + bot scanner)
python main.py --both
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register a new user |
| POST | `/api/auth/login` | Login → JWT tokens |
| POST | `/api/auth/refresh` | Refresh access token |

### User Profile
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/me` | Get current user profile |
| PATCH | `/api/users/me` | Update profile (email, timezone, Telegram ID, etc.) |

### Signals
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/signals` | Create & distribute a signal (admin) |
| GET | `/api/signals` | List signals (filter by type, pair, grade) |
| GET | `/api/signals/{id}` | Get signal details |
| PATCH | `/api/signals/{id}/result` | Update signal outcome (admin) |
| GET | `/api/signals/{id}/deliveries` | Delivery status per channel (admin) |

### Performance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/performance/overview` | Overall win rate, PnL, signal counts |
| GET | `/api/performance/pairs` | Per-pair performance breakdown |
| GET | `/api/performance/leaderboard` | Top pairs by win rate |
| GET | `/api/performance/win-rates` | Win rates for 1d, 7d, 30d |

### Subscriptions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/subscriptions/plans` | List subscription plans |
| POST | `/api/subscriptions/payments` | Create a payment |
| POST | `/api/subscriptions/payments/{id}/confirm` | Confirm payment (admin) |
| GET | `/api/subscriptions/billing` | Billing history |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/dashboard` | Dashboard stats (users, revenue, signals) |
| GET | `/api/admin/users` | List all users |
| PATCH | `/api/admin/users/{id}` | Update user (tier, active, admin) |
| POST | `/api/admin/deliveries/retry` | Retry failed deliveries |
| POST | `/api/admin/performance/snapshot` | Generate performance snapshot |

Interactive API docs are available at `/docs` (Swagger UI) when the server is running.

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/` | Real-time web dashboard (HTML) |

## Signal Types

### Crypto Trading Signals
```
🚀 CRYPTO TRADING SIGNAL [A]

Pair: BTC/USDT
Direction: BUY
Entry: $42,500.00

Targets:
├─ TP1: $43,000.00
├─ TP2: $43,500.00
└─ TP3: $44,000.00

Stop Loss: $42,000.00
R/R Ratio: 1:1.0

Confidence: 85%
Reason: RSI oversold, BB lower band touch, EMA crossover
Valid Until: 2025-01-15 18:00 UTC
```

### Binary Trading Signals
```
⚡ BINARY TRADING SIGNAL [A]

Pair: EUR/USD
Direction: 🟢 CALL
Entry: $1.09
Duration: 5 min

Confidence: 78%
Reason: RSI oversold bounce, support level
Valid Until: 2025-01-15 16:10 UTC
```

## Signal Grades

| Grade | Criteria | Access |
|-------|----------|--------|
| **A+** | Confidence ≥ 85% AND pair win-rate ≥ 70% | Free, Premium, VIP |
| **A** | Confidence ≥ 75% OR pair win-rate ≥ 60% | Free, Premium, VIP |
| **B** | Confidence ≥ 60% | Premium, VIP |
| **C** | Below thresholds | VIP only |

## Subscription Tiers

| Plan | Price/mo | Signals/day | Features |
|------|----------|-------------|----------|
| **Free** | $0 | 3 | Crypto signals, Telegram, basic analytics |
| **Premium** | $29.99 | 20 | + Binary signals, Discord, full analytics, A/B grades |
| **VIP** | $79.99 | Unlimited | + All channels, all grades, API access, priority support |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BINANCE_API_KEY` | Binance API key | — |
| `BINANCE_API_SECRET` | Binance API secret | — |
| `FINNHUB_API_KEY` | Finnhub API key (news) | — |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | — |
| `TELEGRAM_CHAT_ID` | Telegram chat ID (legacy) | — |
| `BROADCAST_TELEGRAM_CHANNELS` | Comma-separated channel IDs | — |
| `DISCORD_WEBHOOK_URL` | Discord webhook for broadcasts | — |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` | Email delivery | — |
| `DATABASE_URL` | Database connection string | `sqlite:///trading_bot.db` |
| `JWT_SECRET` | JWT signing secret (**change in production**) | `change-me-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `60` |
| `API_HOST` / `API_PORT` | API server bind address | `0.0.0.0:8000` |
| `TRADING_MODE` | `paper` or `live` | `paper` |
| `LOG_LEVEL` | Logging level | `INFO` |

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
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.1%}")
```

## Security Notes

- **Never** commit your `.env` file to version control.
- Change `JWT_SECRET` to a strong random value in production.
- Use environment variables or a secrets manager for API keys.
- Always test with `TRADING_MODE=paper` before enabling live trading.
- Start with small position sizes and monitor performance.

## Advanced Features

### AI/ML Prediction Engine
The bot includes a 3-model voting ensemble that runs on CPU (no GPU needed):
- **LightGBM** – fast gradient boosting (10x faster than XGBoost)
- **Random Forest** – robust tree ensemble
- **Gradient Boosting** – scikit-learn classic boosting

Models are trained on ~20 engineered features (returns, volatility, volume ratios, RSI, MACD, EMA distances, candle patterns). Trained models are cached to disk for instant reloads.

### Multi-Timeframe Analysis
Analyses three timeframes simultaneously (5m, 1h, 4h) with weighted consensus:
- Higher timeframes carry more weight (4h: 45%, 1h: 35%, 5m: 20%)
- Full alignment boosts signal confidence by 5%
- Conflicting timeframes reduce confidence by 30%

### On-Chain & Whale Tracking
Monitors blockchain activity using free public APIs:
- Large BTC/ETH transactions (whale movements)
- Exchange inflow/outflow classification (bearish/bullish)
- Network hash rate, transaction counts, mempool size
- On-chain sentiment scoring

### Supply/Demand Zones & Order Blocks
Advanced price action analysis:
- **Supply zones** – areas where strong selling occurred (bearish pressure)
- **Demand zones** – areas where strong buying occurred (bullish pressure)
- **Bullish order blocks** – last bearish candle before a strong up-move
- **Bearish order blocks** – last bullish candle before a strong down-move

### Binary Trading Signals
Full support for binary options platforms (IQ Option, Pocket Option):
- Short-term CALL/PUT signals (30s to 5min expiry)
- Fast indicators optimized for short timeframes (EMA 5/10/20)
- Higher confidence threshold (70%+) for better win rates
- Signal strength classification (STRONG / MODERATE / WEAK)

## License

This project is provided as-is for educational and personal use. Use at your own risk. Cryptocurrency trading involves significant financial risk.
