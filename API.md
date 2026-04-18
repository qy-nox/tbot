# Internal API Documentation

## Health
- `GET /api/health` → service health and database status.

## Signals
- `GET /api/signals` → latest signals.
- `GET /dashboard/api/signals` → dashboard polling payload.

## Dashboard
- `GET /dashboard/` → HTML dashboard.
- `GET /dashboard/backend/market` → market summary payload.

## Admin
- `GET /admin/` → admin dashboard HTML.

## Internal Services
- `services/user_service.py` → user create/fetch helper.
- `services/subscription_service.py` → tier subscription create flow.
- `services/payment_service.py` → payment submission for Binance/bKash/manual bank.
- `services/signal_service.py` → signal generation with B/A/A+ evaluation.
- `services/distribution_service.py` → 12-group routing selector.
- `services/market_data_service.py` → websocket client factory.
