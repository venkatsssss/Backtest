
# SageForge Backtesting Module - Configuration Settings

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Angel One API Settings
    ANGEL_ONE_API_KEY = os.getenv('ANGEL_ONE_API_KEY')
    ANGEL_ONE_CLIENT_ID = os.getenv('ANGEL_ONE_CLIENT_ID')
    ANGEL_ONE_PASSWORD = os.getenv('ANGEL_ONE_PASSWORD')
    ANGEL_ONE_TOTP_SECRET = os.getenv('ANGEL_ONE_TOTP_SECRET')
    
    # Database Settings
    MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'sageforge_backtesting')
    
    # Server Settings
    HOST = os.getenv('HOST', 'localhost')
    PORT = int(os.getenv('PORT', 8000))
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Cache Settings
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    CACHE_EXPIRY = int(os.getenv('CACHE_EXPIRY', 3600))
    
    # Backtesting Default Settings
    DEFAULT_INITIAL_CAPITAL = float(os.getenv('DEFAULT_INITIAL_CAPITAL', 100000))
    DEFAULT_COMMISSION = float(os.getenv('DEFAULT_COMMISSION', 0.0003))
    DEFAULT_SLIPPAGE = float(os.getenv('DEFAULT_SLIPPAGE', 0.001))
    
    # Rate Limiting
    API_RATE_LIMIT = int(os.getenv('API_RATE_LIMIT', 100))
    WEBSOCKET_RATE_LIMIT = int(os.getenv('WEBSOCKET_RATE_LIMIT', 20))
    
    # NSE Trading Hours
    MARKET_OPEN_TIME = "09:15"
    MARKET_CLOSE_TIME = "15:30"
    
    # Supported Exchanges
    SUPPORTED_EXCHANGES = ['NSE', 'BSE']
    
    # Candlestick Patterns Configuration
    CANDLESTICK_PATTERNS = {
        'single': ['HAMMER', 'DOJI', 'SHOOTING_STAR', 'SPINNING_TOP'],
        'double': ['ENGULFING_BULL', 'ENGULFING_BEAR', 'PIERCING_LINE'],
        'triple': ['MORNING_STAR', 'EVENING_STAR', 'THREE_WHITE_SOLDIERS']
    }
    
    # Technical Indicators Configuration
    DEFAULT_INDICATORS = {
        'SMA': [5, 10, 20, 50, 200],
        'EMA': [9, 12, 21, 26],
        'RSI': [14],
        'MACD': {'fast': 12, 'slow': 26, 'signal': 9}
    }

# Initialize configuration
config = Config()


