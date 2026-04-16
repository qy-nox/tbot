from core.advanced_signals import AdvancedSignalGenerator
from core.data_fetcher import DataFetcher

fetcher = DataFetcher()
df = fetcher.fetch_ohlcv("BTC/USDT", timeframe="1h", limit=500)
print(AdvancedSignalGenerator().generate("BTC/USDT", df))
