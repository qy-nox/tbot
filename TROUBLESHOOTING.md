# Troubleshooting

## `ModuleNotFoundError: signal_platform...`
Ensure you're running from project root and dependencies are installed:

```bash
pip install -r requirements.txt
```

## API won't start
Check `.env` values and port conflicts (`API_PORT`, default `8000`).

## No signal deliveries
- Verify user channel fields (`telegram_chat_id`, `email`, etc.)
- Verify delivery credentials (`TELEGRAM_BOT_TOKEN`, `DISCORD_WEBHOOK_URL`, SMTP vars)

## DB errors
Run:

```bash
python -m database.init_db
```
