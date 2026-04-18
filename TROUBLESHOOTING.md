# Troubleshooting

## Telegram 400 Bad Request
- Confirm `TELEGRAM_BOT_TOKEN` format (`<id>:<token>`).
- Confirm `TELEGRAM_CHAT_ID` or broadcast group IDs are numeric.
- If error is `Bad Request: chat not found`, run:
  - `python scripts/get_group_ids.py`
  - `python scripts/setup_groups_wizard.py`
  - `python scripts/verify_groups.py --send-test`
- Ensure bot is added to each group and has admin rights.
- Retry send without parse mode if message contains malformed HTML.

## Port 8000 already in use
- Stop stale process and restart one API instance only.
- Verify supervisor/systemd is not launching duplicate API workers.

## No signals visible
- Check scanner logs for data source failures.
- Confirm DB initialization and signal approval status.
- Check `/api/signals` and `/dashboard/api/signals` payloads.

## Payment queue stuck
- Inspect `payments` and `payment_queue` rows for pending status.
- Verify transaction ID uniqueness and admin verification path.

## WebSocket stream interruptions
- Verify outbound access to Binance websocket endpoints.
- Monitor reconnect logs and tune reconnect delay if needed.

## Database lock/contention
- For SQLite, avoid multi-writer contention and keep transactions short.
- Move to managed Postgres for production multi-process workloads.
