# Setup Guide

## 1) Install

```bash
git clone https://github.com/qy-nox/tbot.git
cd tbot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2) Configure

```bash
cp .env.example .env
# set API keys, DB URL and JWT secret
# bot tokens are optional; bots without valid tokens are skipped by run.py
```

## 3) Initialize DB

```bash
python -m database.init_db
```

## 4) Run services

```bash
# API only
python main.py --api

# scanner only
python main.py

# both together
python main.py --both

# ecosystem manager (API + available bots)
python run.py
```

## 5) Use dashboard/docs

- Dashboard: `http://localhost:8000/dashboard/`
- API docs: `http://localhost:8000/docs`
