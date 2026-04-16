# API Documentation

Base URL: `http://localhost:8000`

## Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/refresh`

## Users
- `GET /api/users/me`
- `PATCH /api/users/me`

## Signals
- `POST /api/signals`
- `GET /api/signals`
- `GET /api/signals/{id}`
- `PATCH /api/signals/{id}/result`
- `GET /api/signals/{id}/deliveries`

## Subscriptions
- `GET /api/subscriptions/plans`
- `POST /api/subscriptions/payments`
- `POST /api/subscriptions/payments/{id}/confirm`
- `GET /api/subscriptions/billing`

## Performance
- `GET /api/performance/overview`
- `GET /api/performance/pairs`
- `GET /api/performance/leaderboard`
- `GET /api/performance/win-rates`

## Admin
- `GET /api/admin/dashboard`
- `GET /api/admin/users`
- `PATCH /api/admin/users/{id}`
- `POST /api/admin/deliveries/retry`
- `POST /api/admin/performance/snapshot`
