# Complete Multi-Bot Trading Signal Platform Architecture

This document describes the full ecosystem architecture supported by this repository:

## Core Components

1. **Bot 1 – Subscription & Payment**
   - onboarding, plan selection, payment verification, activation, welcome flow
2. **Bot 2 – User Management & Admin Control**
   - admin commands, approvals, bans, group control, reminders, exports, analytics
3. **Bot 3 – Signal Distribution & Validation**
   - signal intake, quality grading, tier-based formatting, channel fanout, rate limiting
4. **Admin Website (FastAPI + dashboard UI)**
   - user/payment/group/signal control and analytics endpoints
5. **Mobile App clients**
   - auth, subscription view, signal history, performance tracking, notifications
6. **Unified PostgreSQL schema**
   - users, subscriptions, payments, groups, user_groups, signals, distributions, results, logs, revenue tracking

## End-to-End Flow

1. User starts in subscription flow (Bot 1)
2. Payment is created and verified
3. Approved subscription is synchronized to user management (Bot 2)
4. Signal engine generates candidates and grades confidence
5. Distribution layer (Bot 3) applies plan rules/limits and publishes per channel
6. Outcomes and delivery events are written to the database
7. API/dashboard/mobile surfaces read unified analytics and account state

## Profitability & Risk

The platform is a decision-support and signal-delivery system, not a guaranteed-profit engine.
Performance depends on market regime, execution, and risk discipline.
