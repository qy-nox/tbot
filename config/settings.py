import os

# API Keys
API_KEY = os.environ.get('API_KEY')
API_SECRET = os.environ.get('API_SECRET')

# Trading Parameters
TRADING_PAIR = 'BTC/USD'
ORDER_TYPE = 'market'  # Can also be 'limit'

# Indicator Settings
INDICATOR_SETTINGS = {
    'moving_average_period': 14,
    'rsi_period': 14,
    'bollinger_bands': {
        'window': 20,
        'std_dev': 2,
    },
}

# Risk Management Thresholds
RISK_MANAGEMENT = {
    'stop_loss_percentage': 0.02,  # 2%
    'take_profit_percentage': 0.05,  # 5%
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'DEBUG',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
}