"""
🚀 tbot - Complete Trading Signal Ecosystem
Run ALL 3 bots + API + Dashboard with one command!

Usage: python run.py
"""

import os
import sys
import subprocess
import time
import signal
import logging
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
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
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
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
            },
            {
                "name": "💳 Bot 2: Subscription Bot",
                "cmd": [sys.executable, "-m", "bots.bot_subscription.main"],
                "description": "Payment & subscription management",
            },
            {
                "name": "👨‍💼 Bot 3: Admin Bot",
                "cmd": [sys.executable, "-m", "bots.bot_admin.main"],
                "description": "Admin controls & management",
            },
        ]
    
    def start_all(self):
        """Start all bots"""
        logger.info("=" * 70)
        logger.info("🚀 TBOT ECOSYSTEM v2.0 - STARTING ALL SERVICES")
        logger.info("=" * 70)
        
        for i, bot in enumerate(self.bots, 1):
            try:
                logger.info(f"\n[{i}/{len(self.bots)}] Starting: {bot['name']}")
                logger.info(f"    📝 {bot['description']}")
                logger.info(f"    🔧 Command: {' '.join(bot['cmd'])}")
                
                process = subprocess.Popen(
                    bot['cmd'],
                    cwd=PROJECT_ROOT,
                    start_new_session=True,
                )
                
                self.processes.append(process)
                logger.info(f"    ✅ Started (PID: {process.pid})")
                
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
        logger.info("\n📱 ACCESS YOUR SYSTEM:")
        logger.info("  • Dashboard: http://localhost:8000/dashboard/")
        logger.info("  • API Docs: http://localhost:8000/docs")
        logger.info("  • API Health: http://localhost:8000/api/health")
        logger.info("\n🤖 TELEGRAM BOTS:")
        logger.info("  • Bot 1: @YourMainBotName (live signals)")
        logger.info("  • Bot 2: @YourSubBotName (subscriptions)")
        logger.info("  • Bot 3: @YourAdminBotName (admin)")
        logger.info("\n💡 Press Ctrl+C to stop all services")
        logger.info("=" * 70 + "\n")
        
        # Keep running
        self.monitor()
    
    def monitor(self):
        """Monitor all processes"""
        try:
            while True:
                # Check if any process died
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        logger.warning(f"⚠️  Bot {i+1} terminated (exit code: {process.returncode})")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\n\n🛑 Shutting down all services...")
            self.cleanup()
    
    def cleanup(self):
        """Stop all processes"""
        for i, process in enumerate(self.processes):
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
