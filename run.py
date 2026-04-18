"""
🚀 tbot - Complete Trading Signal Ecosystem
Run API + Dashboard + Telegram bots with one command!

Usage: python run.py
"""

import os
import sys
import subprocess
import time
import signal
import logging
import threading
from pathlib import Path
from typing import Any

from config.settings import Settings, is_valid_telegram_token

# Configure logging (console + file)
_log_file = Path(__file__).resolve().parent / "logs" / "runner.log"
_log_file.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_log_file, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)

# Verify critical files
REQUIRED_FILES = ['.env', 'requirements.txt', 'main.py']
for file in REQUIRED_FILES:
    if not (PROJECT_ROOT / file).exists():
        logger.error(f"❌ Missing required file: {file}")
        sys.exit(1)

class BotManager:
    """Manage all tbot processes"""
    NO_TOKEN_REQUIRED = "__NO_TOKEN_REQUIRED__"
    
    def __init__(self):
        self._lock = threading.Lock()
        self.processes: list[dict[str, Any]] = []
        raw_restart_limit = os.getenv("BOT_RESTART_LIMIT", "3")
        try:
            self.max_restarts = max(0, int(raw_restart_limit))
        except ValueError:
            logger.warning("⚠️ Invalid BOT_RESTART_LIMIT=%r; defaulting to 3", raw_restart_limit)
            self.max_restarts = 3
        self._env_file_cache: dict[str, str] | None = None
        self.bots = [
            {
                "name": "🎯 API Server + Dashboard",
                "cmd": [sys.executable, "main.py", "--both"],
                "description": "Main API and trading bot",
            },
            {
                "name": "📊 Bot 1: Main Signal Bot",
                "cmd": [sys.executable, "-m", "bots.bot_main.main"],
                "description": "Live market data & signals",
                "token_envs": ("TELEGRAM_BOT_TOKEN_MAIN", "TELEGRAM_BOT_TOKEN"),
            },
            {
                "name": "💳 Bot 2: Subscription Bot",
                "cmd": [sys.executable, "-m", "bots.bot_subscription.main"],
                "description": "Payment & subscription management",
                "token_envs": ("TELEGRAM_BOT_TOKEN_SUB", "BOT1_SUBSCRIPTION_TOKEN"),
            },
        ]

    def _load_env_file(self) -> dict[str, str]:
        if self._env_file_cache is not None:
            return self._env_file_cache

        values: dict[str, str] = {}
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                values[key.strip()] = value.strip().strip("'\"")
        self._env_file_cache = values
        return values

    def _get_bot_token(self, bot: dict[str, Any]) -> str | None:
        token_keys = bot.get("token_envs")
        if not token_keys:
            return self.NO_TOKEN_REQUIRED

        env_file_values = self._load_env_file()
        for key in token_keys:
            token = (os.getenv(key) or env_file_values.get(key) or "").strip()
            if token and ":" in token:
                return token
        return None

    @staticmethod
    def _check_db_health() -> bool:
        try:
            from sqlalchemy import text
            from utils.database import get_session, init_db
            init_db()
            db = get_session()
            try:
                db.execute(text("SELECT 1"))
            finally:
                db.close()
            return True
        except Exception as exc:
            logger.error("❌ Database health check failed: %s", exc)
            return False

    def _start_process(self, bot: dict[str, Any], index: int) -> subprocess.Popen:
        logger.info(f"\n[{index}/{len(self.bots)}] Starting: {bot['name']}")
        logger.info(f"    📝 {bot['description']}")
        logger.info(f"    🔧 Command: {' '.join(bot['cmd'])}")

        process = subprocess.Popen(
            bot['cmd'],
            cwd=PROJECT_ROOT,
            start_new_session=True,
        )
        logger.info(f"    ✅ Started (PID: {process.pid})")
        return process
    
    def start_all(self):
        """Start all bots"""
        logger.info("=" * 70)
        logger.info("🚀 TBOT ECOSYSTEM v2.0 - STARTING ALL SERVICES")
        logger.info("=" * 70)
        
        if not self._check_db_health():
            logger.error("❌ Startup aborted due to failing database health check")
            sys.exit(1)

        for i, bot in enumerate(self.bots, 1):
            try:
                token = self._get_bot_token(bot)
                if token is None:
                    logger.warning(f"    ⏭️  Skipping {bot['name']} - no token configured")
                    continue
                if token != self.NO_TOKEN_REQUIRED and not is_valid_telegram_token(token):
                    logger.warning(f"    ⏭️  Skipping {bot['name']} - invalid token format")
                    continue

                process = self._start_process(bot, i)
                with self._lock:
                    self.processes.append({"process": process, "bot": bot, "restarts": 0})
                
                # Wait between starting bots
                if i < len(self.bots):
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"    ❌ Failed to start: {e}")
                self.cleanup()
                sys.exit(1)
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ ALL SERVICES STARTED SUCCESSFULLY!")
        logger.info("=" * 70)
        api_host = Settings.API_HOST if Settings.API_HOST != "0.0.0.0" else "localhost"
        api_port = Settings.API_PORT
        logger.info("\n📱 ACCESS YOUR SYSTEM:")
        logger.info("  • Dashboard: http://%s:%s/dashboard/", api_host, api_port)
        logger.info("  • API Docs: http://%s:%s/docs", api_host, api_port)
        logger.info("  • API Health: http://%s:%s/api/health", api_host, api_port)
        logger.info("\n🤖 TELEGRAM BOTS:")
        logger.info("  • Bot 1: @YourMainBotName (live signals)")
        logger.info("  • Bot 2: @YourSubBotName (subscriptions)")
        logger.info("\n🛠️ ADMIN:")
        logger.info("  • Admin Website: http://%s:%s/admin/", api_host, api_port)
        logger.info("\n💡 Press Ctrl+C to stop all services")
        logger.info("=" * 70 + "\n")
        
        # Keep running
        self.monitor()
    
    def monitor(self):
        """Monitor all processes"""
        try:
            while True:
                # Check if any process died
                with self._lock:
                    snapshot = list(self.processes)
                for process_info in snapshot:
                    if process_info.get("disabled"):
                        continue

                    process = process_info["process"]
                    if process.poll() is None:
                        continue

                    bot_name = process_info["bot"]["name"]
                    restarts = process_info["restarts"]
                    logger.warning(f"⚠️  {bot_name} terminated (exit code: {process.returncode})")

                    if restarts >= self.max_restarts:
                        with self._lock:
                            process_info["disabled"] = True
                        logger.error(f"❌ {bot_name} reached restart limit ({self.max_restarts})")
                        continue

                    logger.info(f"🔁 Restarting {bot_name} (attempt {restarts + 1}/{self.max_restarts})")
                    # Exponential backoff per retry attempt, capped at 60s.
                    backoff_seconds = min(2 ** (restarts + 1), 60)
                    logger.info(f"    ⏱️ Backoff: waiting {backoff_seconds}s before restart")
                    time.sleep(backoff_seconds)
                    restarted = subprocess.Popen(
                        process_info["bot"]["cmd"],
                        cwd=PROJECT_ROOT,
                        start_new_session=True,
                    )
                    with self._lock:
                        process_info["process"] = restarted
                        process_info["restarts"] = restarts + 1
                    logger.info(f"    ✅ Restarted {bot_name} (PID: {restarted.pid})")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Shutting down all services...")
            self.cleanup()
    
    def cleanup(self):
        """Stop all processes"""
        with self._lock:
            snapshot = list(self.processes)
        for i, process_info in enumerate(snapshot):
            process = process_info["process"]
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"   ✅ Stopped Bot {i+1}")
                time.sleep(0.5)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass
        
        logger.info("✅ All services stopped successfully!")

def main():
    """Entry point"""
    try:
        manager = BotManager()
        manager.start_all()
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
