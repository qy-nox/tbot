# ✅ tbot Production Setup Complete

This repository includes:

- `run.py` process manager that starts API/dashboard + all 3 Telegram bots
- completed async bot entrypoints:
  - `bots/bot_main/main.py`
  - `bots/bot_subscription/main.py`
  - `bots/bot_admin/main.py`
- package markers (`__init__.py`) for bot packages
- token validation and structured startup errors
- combined database bootstrap via `utils/database_v2.py`
- full environment template in `.env.example`

## Quick Start

1. Copy environment template:
   - `cp .env.example .env`
2. Configure Telegram tokens and admin IDs in `.env`.
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Initialize database:
   - `python -c "from utils.database_v2 import init_db; init_db()"`
5. Run full ecosystem:
   - `python run.py`

## Access

- Dashboard: `http://localhost:8000/dashboard/`
- API docs: `http://localhost:8000/docs`

