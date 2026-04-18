# TBOT Telegram Trading Ecosystem

TBOT is a production-oriented Telegram trading ecosystem that combines signal generation, payment onboarding, subscription control, and multi-group delivery into one deployable stack. The repository includes an API service, dashboard pages, bot packages, and operational scripts designed so teams can bootstrap quickly and still keep architecture modular. The project is intentionally environment-driven and avoids hardcoded secrets, allowing the same codebase to run in local development, staging, and production with only configuration changes.

The ecosystem is structured around three bot roles. The main signal bot focuses on market-facing signal workflows and user-facing updates. The subscription bot handles onboarding, payment capture, and renewal status communication. The admin bot provides operational controls, health views, and moderation hooks for user and signal governance. Even when operators prefer the web dashboard for daily tasks, keeping a dedicated admin bot package helps preserve deployment symmetry and enables future command-based operations without disruptive refactors.

## Architecture Overview

The platform is split into clear layers: bot adapters, service layer, data layer, and web interface. Bot adapters transform Telegram interactions into internal service calls. The service layer enforces business rules such as signal grading thresholds, subscription lifecycle transitions, and distribution targeting. The data layer stores durable records for users, subscriptions, signals, distribution outcomes, payments, and verification queues. The web interface exposes monitoring and control capabilities through API-backed pages and static assets.

The same deployment can run a single process in lightweight environments or separate services in production. For example, a small team may use `python run.py` for all-in-one operation, while production can use systemd units or containerized process groups with dedicated restart policies. This dual model keeps onboarding easy while preserving a clear path to reliability improvements such as horizontal scaling, service-level monitoring, and controlled rollouts.

## Three Telegram Bots

### 1. Main Signal Bot
The main signal bot presents market snapshots, active signal views, and performance summaries. It routes commands through handlers and composes user-facing messages using consistent formatting. A compatibility package is provided at `bots/main_signal_bot` for production-style naming while preserving existing internal functionality under `bots/bot_main`.

### 2. Subscription Bot
The subscription bot package receives plan selection actions, guides users through payment submission, and shares current subscription status. Payment options support Binance P2P, bKash, and manual bank transfer workflows. The compatibility package at `bots/subscription_bot` is aligned for integration tests and deployment scripts.

### 3. Admin Bot
The admin bot package centralizes operational functions including user lookup, signal listing, and dashboard-style analytics output. In many deployments, teams use the web admin page as the primary panel, but a dedicated admin bot package (`bots/admin_bot`) keeps command automation and incident workflows possible from Telegram if needed.

## Signal Engine and Quality Model

Signals are graded with requirement-aligned thresholds using a dedicated engine: B grade for baseline confidence and confirmation, A grade for stronger multi-indicator agreement, and A+ grade for high-confidence, high-confirmation events. The implementation in `bots/main_signal_bot/signal_engine.py` standardizes this logic so downstream services can rely on a single evaluation contract.

The engine returns grade, normalized confidence, and expected accuracy tier. This makes messaging, storage, and routing deterministic across components. Teams can tune confidence and confirmation inputs from strategy modules without touching distribution or subscription code. This separation lowers regression risk and supports faster experimentation.

## Real-Time Market Data

The market data module includes a Binance websocket client with automatic reconnect behavior. It is intentionally lightweight and callback-driven so consumers can wire in analytics, alerting, or persistence with minimal coupling. Reconnect handling is explicit, and stream shutdown can be requested gracefully.

In production, websocket clients should be supervised by either process managers or async schedulers. The included scheduler helper demonstrates recurring task orchestration and graceful cancellation. This pattern supports health checks and clean shutdown, which are critical for preserving reliability during deploys or node restarts.

## Group Distribution Strategy

Twelve managed groups are represented as typed definitions covering crypto/binary, grade tiers, and audience split (HV/VIP). The distribution helper selects target groups by signal type and grade, enabling deterministic routing. This design keeps routing logic transparent and testable while allowing future extension for geography, language, or campaign tags.

Operators can seed and maintain group metadata via scripts and database records. Since group IDs live in environment variables and database tables, configuration can evolve without code edits. This is important when Telegram groups are rotated, renamed, or segmented based on capacity and policy.

## Payment and Subscription Workflows

The subscription layer models payment submission, verification queueing, and tier activation. Binance P2P, bKash, and manual bank transfer are normalized under a common payment service contract. Verification can be automated for selected providers or routed to admin approval queues where regulations or business controls require manual checks.

The database model includes payments and payment queue tables with timestamps for submission, verification, and rejection. This audit-friendly structure supports troubleshooting and operational reporting. It also allows building SLA dashboards for payment approval latency and failure rates.

## Database Schema

The compatibility schema in `database/models.py` defines Users, Subscriptions, Signals, SignalDistribution, Groups, Payments, and PaymentQueue. These tables align with Telegram-first trading operations and include lifecycle fields such as status, verification markers, and expiry windows. The schema is SQLAlchemy-based and can be initialized through `database/queries.py` and `scripts/init_db.py`.

While the repository also includes existing platform models under `signal_platform`, this compatibility layer is useful for integrations requiring explicit table names and fields from specification-driven contracts. Teams can choose one schema path or map between them during migration windows.

## Website and Dashboard Surface

A static website bundle (`website/`) provides landing, signals, and pricing pages with lightweight JavaScript refresh logic. It is intended as a deployment-ready starter, not a locked final design, so teams can swap branding and copy quickly. The included `vercel.json` demonstrates straightforward static hosting rewrites.

The broader repository already ships dashboard and admin static pages under `signal_platform/static` and `dashboard/frontend`, which can be run together with API routes for richer operational visibility. The added website pages mainly satisfy public-facing marketing and onboarding requirements.

## Configuration Strategy

All secrets and runtime toggles are environment-driven through `config/settings.py` and `.env.example`. New fields include three-bot token aliases, payment provider credentials, and 12 managed group IDs. Configuration validation helpers guard against malformed Telegram token/chat values, reducing silent runtime failure modes.

For production, use secret managers or encrypted environment injection rather than plain text files. Keep `.env.example` as non-sensitive documentation only. The logger utility masks common secret patterns and configured key values to prevent accidental leakage in logs.

## Operations and Deployment

Deployment options include Docker, docker-compose, and systemd service units. Systemd files for each bot process are provided under `configs/systemd/`. Scripts support DB initialization, default group creation, and starting all services. Combined with health endpoints and structured logs, this setup covers most single-node production requirements.

For high-availability environments, run bots and API separately, use managed databases, and aggregate logs centrally. Add monitoring around queue growth, websocket reconnect frequency, API latency, and signal throughput. Backup strategy should include both database snapshots and environment configuration artifacts.

## Setup Guide

1. Copy environment template: `cp .env.example .env`
2. Install dependencies: `pip install -r requirements.txt`
3. Initialize schema: `python scripts/init_db.py`
4. Seed managed groups: `python scripts/create_groups.py`
5. Start ecosystem: `python scripts/start_all.py` or `python run.py`

After startup, validate `/api/health`, dashboard routes, and Telegram bot connectivity. For first-run Telegram testing, verify chat IDs and send a lightweight confirmation message before enabling broad signal fanout.

## Reliability and Error Handling

The codebase uses structured exception handling for network/API boundaries, graceful websocket reconnect loops, database transaction boundaries, and startup config validation. Retry policies are present in notifier and stream components. Process supervision is available through both run manager and systemd restart settings.

Teams should extend observability with alerting on repeated payment verification failures, distribution send errors, and sustained scanner latency. Incident response playbooks should include token rotation, group ID validation, and emergency disable switches for outbound signal delivery.

## Security Notes

Do not commit live tokens or private keys. Keep principle of least privilege for exchange and payment credentials. Use HTTPS everywhere external traffic is exposed. If adding admin Telegram commands, enforce explicit admin allowlists and action logging.

The repository already includes validator and security-focused tests. Continue running full tests before deployment and after significant configuration changes. Security scanning and code review should be part of release flow for every PR.

## API and Internal Contracts

See `API.md` for endpoint summaries and service contracts. Core integration points include signal creation, user/subscription management, payment intake, and distribution status tracking. Internal modules prefer small typed functions and wrappers that make transition between old and new package names non-breaking.

Backward compatibility is preserved by keeping existing bot packages in place while adding production-style package aliases. This minimizes migration friction for current deployments while allowing external integrators to target the new standardized paths.

## Troubleshooting Summary

If Telegram messages fail with HTTP 400, validate chat IDs and parse mode payload formatting. If API startup fails on port conflicts, stop stale processes and restart with clean supervision. If payment queues stall, inspect pending rows and verification timestamps. If websocket updates stop, check reconnect logs and outbound network policies.

A longer checklist is in `TROUBLESHOOTING.md`, including database lock handling, token validation, and deployment sanity checks.

## Production Checklist

- [ ] Environment variables validated
- [ ] Database migrations applied
- [ ] Telegram tokens and chat/group IDs verified
- [ ] Payment methods tested end-to-end
- [ ] Signal routing validated for all 12 groups
- [ ] Health and dashboard endpoints reachable
- [ ] Log rotation and retention configured
- [ ] Backup/restore dry run completed
- [ ] Security scan and tests green
- [ ] Rollback plan documented

Following this checklist before every release helps keep signal quality, payment integrity, and user trust stable over time.

## Closing Notes

This repository now provides both legacy-compatible modules and standardized production-style ecosystem paths. The implementation is intentionally incremental so existing users are not disrupted, while new automation and deployment scripts can target the expanded structure immediately. Continue evolving strategy logic, payment adapters, and analytics depth as operational data accumulates.

If you plan a larger platform migration, keep wrappers in place until all external references have moved. That approach avoids breaking downstream bots, cron jobs, and integrations during transition windows.