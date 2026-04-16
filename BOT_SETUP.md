# Bot Setup

## Bot 1 (Subscription)

```bash
python -m bots.bot1_subscription.main --user-id 1 --tier premium
```

## Bot 2 (Admin)

```bash
python -m bots.bot2_admin.main --limit 20
```

## Bot 3 (Distribution)

```bash
python -m bots.bot3_distribution.main --signal-id 1
```

These bot entrypoints are lightweight operational helpers and reuse `signal_platform` services.
