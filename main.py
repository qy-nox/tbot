"""
Main entry point for the Advanced Cryptocurrency Trading Signal Bot.
Runs a continuous loop that scans configured pairs, analyses data,
generates signals, and sends notifications.
"""

import asyncio
import logging
import time
import sys

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


# ── Entry point ─────────────────────────────────────────────────────────

def main() -> None:
    bot = TradingBot()
    bot.run_forever()


if __name__ == "__main__":
    main()
