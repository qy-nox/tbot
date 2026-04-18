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
from datetime import datetime, timedelta, timezone

from config.settings import Settings
from core.exceptions import ValidationError
from core.data_fetcher import DataFetcher
from core.security import ensure_valid_pair
from core.technical_analyzer import TechnicalAnalyzer
from core.sentiment_analyzer import SentimentAnalyzer
from core.multi_timeframe import MultiTimeframeAnalyzer
from core.onchain_analyzer import OnChainAnalyzer
from strategies.strategy_engine import Signal, StrategyEngine
from strategies.binary_strategy import BinaryStrategyEngine
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
        self.binary_strategy = BinaryStrategyEngine(
            expiry=Settings.BINARY_EXPIRY_SECONDS
        )
        self.mtf = MultiTimeframeAnalyzer()
        self.onchain = OnChainAnalyzer()
        self.sizer = PositionSizer()
        self.notifier = TelegramNotifier()
        for error in Settings.validate_startup_config():
            logger.warning("Startup config warning: %s", error)
        logger.info("Startup config: %s", Settings.startup_snapshot())

        # ML engine (lazy-loaded to avoid import errors if deps missing)
        self.ml_engine = None
        if Settings.ML_ENABLED:
            try:
                from core.ml_engine import MLEngine
                self.ml_engine = MLEngine()
                logger.info("ML engine loaded (cached=%s)", self.ml_engine.is_ready)
            except ImportError:
                logger.warning("ML dependencies not installed – ML engine disabled")

        init_db()
        logger.info("Database initialised")

    # ── Single scan cycle ───────────────────────────────────────────────

    def scan_pair(self, pair: str) -> None:
        """Fetch data, analyse, and emit a signal for *pair*."""
        try:
            pair = ensure_valid_pair(pair)
        except ValidationError:
            logger.warning("Rejected invalid trading pair: %r", pair)
            return
        logger.info("Scanning %s …", pair)

        # 1. Fetch OHLCV
        df = self.data_fetcher.fetch_ohlcv(pair)
        if df.empty:
            logger.warning("No data for %s – skipping", pair)
            return

        # 2. Technical analysis
        analysis = self.analyzer.analyse(df)
        if not analysis:
            logger.warning("%s: technical analysis returned no result", pair)
            return
        logger.debug("%s: analysis keys=%s", pair, sorted(analysis.keys()))

        # 3. Multi-timeframe analysis (best-effort)
        mtf_result = None
        try:
            mtf_data = {}
            for tf in Settings.MTF_TIMEFRAMES:
                limit = Settings.MTF_CANDLE_LIMITS.get(tf, 200)
                tf_df = self.data_fetcher.fetch_ohlcv(pair, timeframe=tf, limit=limit)
                if not tf_df.empty:
                    mtf_data[tf] = tf_df
            if mtf_data:
                mtf_result = self.mtf.analyse(mtf_data)
        except Exception:
            logger.warning("Multi-timeframe analysis failed for %s (non-fatal)", pair, exc_info=True)

        # 4. Sentiment analysis (best-effort)
        articles = self.data_fetcher.fetch_crypto_news()
        sentiment_result = self.sentiment.analyse_articles(articles)

        # 5. On-chain analysis (best-effort)
        onchain_sentiment = 0.0
        try:
            asset_name = pair.split("/")[0].lower()
            whales = self.onchain.get_whale_transactions(asset_name)
            onchain_sentiment = self.onchain.analyse_whale_sentiment(whales)
        except Exception:
            logger.warning("On-chain analysis failed for %s (non-fatal)", pair, exc_info=True)

        # 6. ML prediction (best-effort)
        ml_boost = 0.0
        prediction = None
        if self.ml_engine and self.ml_engine.is_ready:
            try:
                prediction = self.ml_engine.predict(df)
                if prediction and prediction.direction != "HOLD":
                    ml_boost = prediction.confidence * 0.1  # small boost
                    logger.info("ML boost for %s: %+.2f (%s)", pair, ml_boost, prediction.direction)
            except Exception:
                logger.warning("ML prediction failed for %s (non-fatal)", pair, exc_info=True)

        # 7. Strategy evaluation
        signal = self.strategy.evaluate(
            pair=pair,
            analysis=analysis,
            sentiment=sentiment_result,
            atr=analysis.get("atr"),
        )
        if signal is None:
            signal = self._fallback_signal(pair, analysis)
            if signal is None:
                logger.info("%s: no signal", pair)
                return
            logger.info("%s: fallback signal generated", pair)

        # Apply MTF alignment boost
        if mtf_result and mtf_result.alignment == "ALIGNED":
            signal.confidence = min(signal.confidence + 0.05, 1.0)
            signal.reasons.append(f"MTF aligned ({mtf_result.dominant_trend})")

        # Apply ML boost if direction agrees
        if ml_boost > 0 and prediction and prediction.direction == signal.direction:
            signal.confidence = min(signal.confidence + ml_boost, 1.0)
            signal.reasons.append("ML ensemble confirms")

        # 8. Position sizing
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

        # 9. Store signal in database
        self._store_signal(signal)

        # 10. Send Telegram notification
        sent_ok = self.notifier.send_signal(signal)
        if not sent_ok:
            logger.warning(
                "%s: telegram notification failed after %d attempts",
                pair,
                max(1, Settings.TELEGRAM_RETRY_ATTEMPTS),
            )

        # 11. Store in platform & distribute to subscribers
        self._platform_distribute(signal, analysis)

        logger.info(
            "Signal stored & notified: %s %s @ %.4f (conf %.0f%%)",
            signal.direction,
            pair,
            signal.entry_price,
            signal.confidence * 100,
        )

    @staticmethod
    def _fallback_signal(pair: str, analysis: dict) -> Signal | None:
        """Generate a conservative fallback signal when consensus returns none."""
        trend = analysis.get("trend")
        close = analysis.get("close")
        atr = analysis.get("atr") or 0.0
        ema_fast = analysis.get("ema_fast")
        ema_medium = analysis.get("ema_medium")

        if trend not in {"UPTREND", "DOWNTREND"} or close is None:
            return None
        if ema_fast is None or ema_medium is None:
            return None

        direction = None
        if trend == "UPTREND" and ema_fast >= ema_medium:
            direction = "BUY"
        elif trend == "DOWNTREND" and ema_fast <= ema_medium:
            direction = "SELL"
        if direction is None:
            return None

        sl_distance = max(float(atr) * Settings.STOP_LOSS_ATR_MULTIPLIER, float(close) * 0.002)
        if direction == "BUY":
            stop_loss = close - sl_distance
            take_profit_1 = close + sl_distance * Settings.TAKE_PROFIT_LEVELS[0]
            take_profit_2 = close + sl_distance * Settings.TAKE_PROFIT_LEVELS[1]
            take_profit_3 = close + sl_distance * Settings.TAKE_PROFIT_LEVELS[2]
        else:
            stop_loss = close + sl_distance
            take_profit_1 = close - sl_distance * Settings.TAKE_PROFIT_LEVELS[0]
            take_profit_2 = close - sl_distance * Settings.TAKE_PROFIT_LEVELS[1]
            take_profit_3 = close - sl_distance * Settings.TAKE_PROFIT_LEVELS[2]

        return Signal(
            timestamp=datetime.now(timezone.utc),
            pair=pair,
            direction=direction,
            entry_price=float(close),
            stop_loss=round(float(stop_loss), 8),
            take_profit_1=round(float(take_profit_1), 8),
            take_profit_2=round(float(take_profit_2), 8),
            take_profit_3=round(float(take_profit_3), 8),
            confidence=max(0.55, Settings.MIN_SIGNAL_CONFIDENCE),
            trend=trend,
            reasons=["Fallback trend signal"],
            strategy_name="fallback_trend",
        )

    # ── Binary signal scan ──────────────────────────────────────────────

    def scan_binary_pair(self, pair: str) -> None:
        """Fetch short-term data and emit a binary CALL/PUT signal."""
        logger.info("Binary scan %s …", pair)

        df = self.data_fetcher.fetch_ohlcv(
            pair,
            timeframe=Settings.BINARY_TIMEFRAME,
            limit=100,
        )
        if df.empty:
            logger.warning("No binary data for %s – skipping", pair)
            return

        signal = self.binary_strategy.evaluate(pair, df)
        if signal is None:
            logger.info("%s: no binary signal", pair)
            return

        # Notify
        self._send_binary_notification(signal)

        # Store in platform
        self._platform_distribute_binary(signal)

        logger.info(
            "Binary signal: %s %s @ %.4f (conf %.0f%%, %s, expiry %ds)",
            signal.direction,
            pair,
            signal.entry_price,
            signal.confidence * 100,
            signal.strength,
            signal.expiry_seconds,
        )

    # ── Full scan across all pairs ──────────────────────────────────────

    def run_scan(self) -> None:
        """Scan every pair in the configured list."""
        logger.info("Starting scan cycle for %d pairs", len(Settings.TRADING_PAIRS))

        # Crypto signals
        for pair in Settings.TRADING_PAIRS:
            try:
                self.scan_pair(pair)
            except Exception:
                logger.exception("Error scanning %s", pair)

        # Binary signals
        if Settings.BINARY_ENABLED:
            logger.info("Starting binary scan for %d pairs", len(Settings.BINARY_PAIRS))
            for pair in Settings.BINARY_PAIRS:
                try:
                    self.scan_binary_pair(pair)
                except Exception:
                    logger.exception("Error in binary scan for %s", pair)

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
            duplicate_since = datetime.now(timezone.utc) - timedelta(
                minutes=Settings.SIGNAL_DEDUP_WINDOW_MINUTES
            )
            existing = (
                session.query(SignalModel)
                .filter(
                    SignalModel.pair == signal.pair,
                    SignalModel.direction == signal.direction,
                    SignalModel.timestamp >= duplicate_since,
                )
                .first()
            )
            if existing is not None:
                logger.info("Skipping duplicate signal for %s (%s)", signal.pair, signal.direction)
                return
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

    # ── Binary notification ─────────────────────────────────────────────

    def _send_binary_notification(self, signal) -> None:
        """Send a formatted binary signal via Telegram."""
        direction_emoji = "\U0001f7e2" if signal.direction == "CALL" else "\U0001f534"
        expiry = signal.expiry_seconds
        if expiry >= 60:
            dur_str = f"{expiry // 60} min"
        else:
            dur_str = f"{expiry} sec"

        text = (
            f"\u26a1 <b>BINARY TRADING SIGNAL</b>\n\n"
            f"<b>Pair:</b> {signal.pair}\n"
            f"<b>Direction:</b> {direction_emoji} {signal.direction}\n"
            f"<b>Entry:</b> {signal.entry_price:,.4f}\n"
            f"<b>Expiry:</b> {dur_str}\n\n"
            f"<b>Confidence:</b> {signal.confidence:.0%}\n"
            f"<b>Strength:</b> {signal.strength}\n\n"
            f"<b>Reason:</b> {'; '.join(signal.reasons)}"
        )
        self.notifier.send_message(text)

    # ── Binary platform distribution ────────────────────────────────────

    @staticmethod
    def _platform_distribute_binary(signal) -> None:
        """Store binary signal in the platform and distribute."""
        try:
            from signal_platform.models import SignalDirection, SignalType
            from signal_platform.models import get_session as platform_session
            from signal_platform.services.signal_service import SignalService
            from signal_platform.services.distribution_service import DistributionService

            db = platform_session()
            try:
                direction = (
                    SignalDirection.BUY
                    if signal.direction == "CALL"
                    else SignalDirection.SELL
                )
                sig = SignalService.create_signal(
                    db,
                    signal_type=SignalType.BINARY,
                    pair=signal.pair,
                    direction=direction,
                    entry_price=signal.entry_price,
                    confidence=signal.confidence,
                    strategy=signal.strategy_name,
                    reason="; ".join(signal.reasons) if signal.reasons else "",
                    binary_duration=signal.expiry_seconds,
                    binary_direction=signal.direction,
                )
                DistributionService.distribute(db, sig)
            finally:
                db.close()
        except Exception:
            logger.exception("Binary platform distribution failed (non-fatal)")


# ── API server ──────────────────────────────────────────────────────────


def start_api() -> None:
    """Start the FastAPI server (blocking)."""
    import os
    import uvicorn
    from signal_platform.models import init_db as platform_init
    from signal_platform.api.app import app

    platform_init()

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    logger.info("Starting API server on %s:%d", host, port)
    uvicorn.run(app, host=host, port=port, log_level="info")


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
