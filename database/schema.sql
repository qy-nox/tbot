-- Canonical schema bootstrap for the signal platform (SQLite/Postgres friendly core)

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  email VARCHAR(120) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT 1,
  is_admin BOOLEAN DEFAULT 0,
  subscription_tier VARCHAR(16) NOT NULL DEFAULT 'free',
  telegram_chat_id VARCHAR(50),
  discord_user_id VARCHAR(50),
  whatsapp_number VARCHAR(20),
  timezone VARCHAR(50) DEFAULT 'UTC',
  language VARCHAR(10) DEFAULT 'en',
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscription_plans (
  id INTEGER PRIMARY KEY,
  tier VARCHAR(16) UNIQUE NOT NULL,
  name VARCHAR(50) NOT NULL,
  price_monthly FLOAT DEFAULT 0,
  price_yearly FLOAT DEFAULT 0,
  max_signals_per_day INTEGER DEFAULT 5,
  features TEXT,
  is_active BOOLEAN DEFAULT 1,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  amount FLOAT NOT NULL,
  currency VARCHAR(10) DEFAULT 'USD',
  provider VARCHAR(20),
  provider_tx_id VARCHAR(120),
  status VARCHAR(20) DEFAULT 'pending',
  subscription_tier VARCHAR(16),
  period_start TIMESTAMP,
  period_end TIMESTAMP,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS signal_records (
  id INTEGER PRIMARY KEY,
  timestamp TIMESTAMP,
  signal_type VARCHAR(16) NOT NULL,
  pair VARCHAR(20) NOT NULL,
  direction VARCHAR(10) NOT NULL,
  entry_price FLOAT NOT NULL,
  stop_loss FLOAT,
  take_profit_1 FLOAT,
  take_profit_2 FLOAT,
  take_profit_3 FLOAT,
  confidence FLOAT,
  grade VARCHAR(8),
  strategy VARCHAR(50),
  reason TEXT,
  valid_until TIMESTAMP,
  risk_reward_ratio FLOAT,
  binary_duration INTEGER,
  binary_direction VARCHAR(10),
  outcome VARCHAR(20) DEFAULT 'pending',
  actual_exit_price FLOAT,
  pnl_percent FLOAT,
  closed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS signal_deliveries (
  id INTEGER PRIMARY KEY,
  signal_id INTEGER NOT NULL REFERENCES signal_records(id) ON DELETE CASCADE,
  user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
  channel VARCHAR(20) NOT NULL,
  channel_target VARCHAR(120),
  status VARCHAR(20) DEFAULT 'pending',
  retry_count INTEGER DEFAULT 0,
  error_message TEXT,
  sent_at TIMESTAMP,
  created_at TIMESTAMP,
  UNIQUE(signal_id, user_id, channel)
);
