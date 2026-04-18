# Setup

1. `cp .env.example .env`
2. `pip install -r requirements.txt`
3. `python scripts/init_db.py`
4. `python scripts/create_groups.py`
5. Create 12 Telegram groups (Crypto/Binary × B/A/A+ × HV/VIP)
6. Add your bot as admin in each group
7. `python scripts/get_group_ids.py`
8. `python scripts/setup_groups_wizard.py`
9. `python scripts/verify_groups.py --send-test`
10. `python scripts/start_all.py`
