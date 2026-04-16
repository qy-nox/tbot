# Deployment Guide

## Local/VM
1. Install Python 3.12+
2. Install dependencies from `requirements.txt`
3. Configure `.env`
4. Run `python -m database.init_db`
5. Start with `python main.py --both`

## Docker

```bash
docker compose up --build
```

Set production secrets (`JWT_SECRET`, API keys, SMTP credentials, bot tokens) via environment variables.
