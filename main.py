"""
Main entry point for the Advanced Cryptocurrency Trading Signal Bot.

Supports two modes:
  python main.py          – Run the trading bot scanner loop
  python main.py --api    – Start the REST API server (platform)
  python main.py --both   – Run both the scanner and the API server
"""

import argparse
import logging
import threading
import time

from config.settings import Settings
from core.data_fetcher import DataFetcher
from core.technical_analyzer import TechnicalAnalyzer
from core.sentiment_analyzer import SentimentAnalyzer
from strategies.strategy_engine import StrategyEngine
from risk_management.position_sizer import PositionSizer
from notifications.telegram_notifier import TelegramNotifier
from utils.database import init_db, get_session, Signal as SignalModel
from utils.logger import setup_logger

logger = setup_logger()


class TradingBot:
    """Orchestrates the trading bot lifecycle."""

    def __init__(self) -> None:
        logger.info("Initialising Trading Bot …")
        self.data_fetcher = DataFetcher()
        self.analyzer = TechnicalAnalyzer()
        self.sentiment = SentimentAnalyzer()
        self.strategy = StrategyEngine()
        self.sizer = PositionSizer()
        self.notifier = TelegramNotifier()

        init_db()
        logger.info("Database initialised")

    # ── Single scan cycle ───────────────────────────────────────────────

    def scan_pair(self, pair: str) -> None:
        """Fetch data, analyse, and emit a signal for *pair*."""
        logger.info("Scanning %s …", pair)

        # 1. Fetch OHLCV
        df = self.data_fetcher.fetch_ohlcv(pair)
        if df.empty:
            logger.warning("No data for %s – skipping", pair)
            return

        # 2. Technical analysis
        analysis = self.analyzer.analyse(df)
        if not analysis:
            return

        # 3. Sentiment analysis (best-effort)
        articles = self.data_fetcher.fetch_crypto_news()
        sentiment_result = self.sentiment.analyse_articles(articles)

        # 4. Strategy evaluation
        signal = self.strategy.evaluate(
            pair=pair,
            analysis=analysis,
            sentiment=sentiment_result,
            atr=analysis.get("atr"),
        )
        if signal is None:
            logger.info("%s: no signal", pair)
            return

        # 5. Position sizing
        plan = self.sizer.compute(
            pair=signal.pair,
            direction=signal.direction,
            entry_price=signal.entry_price,
            atr=analysis.get("atr", 0),
            confidence=signal.confidence,
        )
        if plan is None:
            logger.info("%s: position sizer blocked trade", pair)
            return

        # 6. Store signal in database
        self._store_signal(signal)

        # 7. Send Telegram notification
        self.notifier.send_signal(signal)

        # 8. Store in platform & distribute to subscribers
        self._platform_distribute(signal, analysis)

        logger.info(
            "Signal stored & notified: %s %s @ %.4f (conf %.0f%%)",
            signal.direction,
            pair,
            signal.entry_price,
            signal.confidence * 100,
        )

    # ── Full scan across all pairs ──────────────────────────────────────

    def run_scan(self) -> None:
        """Scan every pair in the configured list."""
        logger.info("Starting scan cycle for %d pairs", len(Settings.TRADING_PAIRS))
        for pair in Settings.TRADING_PAIRS:
            try:
                self.scan_pair(pair)
            except Exception:
                logger.exception("Error scanning %s", pair)
        logger.info("Scan cycle complete")

    # ── Continuous loop ─────────────────────────────────────────────────

    def run_forever(self) -> None:
        """Run scan cycles in a loop with a configurable interval."""
        logger.info(
            "Bot running – scan interval %ds", Settings.SCAN_INTERVAL_SECONDS
        )
        self.notifier.send_message("\u2705 <b>Trading Bot started</b>")

        while True:
            try:
                self.run_scan()
            except KeyboardInterrupt:
                logger.info("Shutdown requested")
                self.notifier.send_message("\U0001f6d1 <b>Trading Bot stopped</b>")
                break
            except Exception:
                logger.exception("Unexpected error in scan cycle")

            logger.info(
                "Sleeping %ds until next scan …", Settings.SCAN_INTERVAL_SECONDS
            )
            time.sleep(Settings.SCAN_INTERVAL_SECONDS)

    # ── Database helper ─────────────────────────────────────────────────

    @staticmethod
    def _store_signal(signal) -> None:
        session = get_session()
        try:
            record = SignalModel(
                pair=signal.pair,
                direction=signal.direction,
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                take_profit_1=signal.take_profit_1,
                take_profit_2=signal.take_profit_2,
                take_profit_3=signal.take_profit_3,
                confidence=signal.confidence,
                strategy=signal.strategy_name,
                reason="; ".join(signal.reasons),
            )
            session.add(record)
            session.commit()
        except Exception:
            session.rollback()
            logger.exception("Failed to store signal")
        finally:
            session.close()

    # ── Platform integration ────────────────────────────────────────────

    @staticmethod
    def _platform_distribute(signal, analysis: dict) -> None:
        """Store in the platform's signal_records table & distribute."""
        try:
            from signal_platform.models import SignalDirection, SignalType
            from signal_platform.models import get_session as platform_session
            from signal_platform.services.signal_service import SignalService
            from signal_platform.services.distribution_service import DistributionService

            db = platform_session()
            try:
                direction = (
                    SignalDirection.BUY
                    if signal.direction.upper() == "BUY"
                    else SignalDirection.SELL
                )
                sig = SignalService.create_signal(
                    db,
                    signal_type=SignalType.CRYPTO,
                    pair=signal.pair,
                    direction=direction,
                    entry_price=signal.entry_price,
                    stop_loss=signal.stop_loss,
                    take_profit_1=signal.take_profit_1,
                    take_profit_2=signal.take_profit_2,
                    take_profit_3=signal.take_profit_3,
                    confidence=signal.confidence,
                    strategy=signal.strategy_name,
                    reason="; ".join(signal.reasons) if signal.reasons else "",
                )
                DistributionService.distribute(db, sig)
            finally:
                db.close()
        except Exception:
            logger.exception("Platform distribution failed (non-fatal)")


# ── API server ──────────────────────────────────────────────────────────


def start_api() -> None:
    """Start the FastAPI server (blocking)."""
    import os
    import uvicorn
    from signal_platform.models import init_db as platform_init

    platform_init()

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    logger.info("Starting API server on %s:%d", host, port)
    uvicorn.run("signal_platform.api.app:app", host=host, port=port, log_level="info")


# ── Entry point ─────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Trading Signal Service Platform")
    parser.add_argument("--api", action="store_true", help="Start REST API server only")
    parser.add_argument("--both", action="store_true", help="Run bot scanner + API server")
    args = parser.parse_args()

    if args.api:
        start_api()
    elif args.both:
        # Start API in a background thread
        api_thread = threading.Thread(target=start_api, daemon=True)
        api_thread.start()
        # Run bot scanner in main thread
        bot = TradingBot()
        bot.run_forever()
    else:
        bot = TradingBot()
        bot.run_forever()


if __name__ == "__main__":
    main()
