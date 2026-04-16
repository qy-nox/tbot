from backtesting.advanced_backtest_engine import AdvancedBacktestEngine
from core.data_fetcher import DataFetcher

fetcher = DataFetcher()
df = fetcher.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=500)
engine = AdvancedBacktestEngine()
print(engine.run(df))
