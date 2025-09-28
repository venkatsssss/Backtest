import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Production-ready configuration for SageForge"""
    
    # Angel One API Settings (REQUIRED for production)
    ANGEL_ONE_API_KEY = os.getenv('ANGEL_ONE_API_KEY')
    ANGEL_ONE_CLIENT_ID = os.getenv('ANGEL_ONE_CLIENT_ID')
    ANGEL_ONE_PASSWORD = os.getenv('ANGEL_ONE_PASSWORD')
    ANGEL_ONE_TOTP_SECRET = os.getenv('ANGEL_ONE_TOTP_SECRET')
    
    # Validate required Angel One credentials
    @classmethod
    def validate_angel_credentials(cls):
        required_fields = [
            'ANGEL_ONE_API_KEY',
            'ANGEL_ONE_CLIENT_ID', 
            'ANGEL_ONE_PASSWORD',
            'ANGEL_ONE_TOTP_SECRET'
        ]
        missing = [field for field in required_fields if not getattr(cls, field)]
        if missing:
            raise ValueError(f"Missing required Angel One credentials: {missing}")
    
    # Server Settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # API Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
    RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 3600))  # 1 hour
    
    # Angel One API Constraints
    MAX_REQUESTS_PER_SECOND = 10
    MAX_HISTORICAL_REQUESTS_PER_MINUTE = 200
    REQUEST_DELAY = 0.1  # 100ms between requests
    
    # Trading Configuration
    DEFAULT_INITIAL_CAPITAL = float(os.getenv('DEFAULT_INITIAL_CAPITAL', 100000))
    DEFAULT_COMMISSION = float(os.getenv('DEFAULT_COMMISSION', 0.0003))  # 0.03%
    DEFAULT_SLIPPAGE = float(os.getenv('DEFAULT_SLIPPAGE', 0.001))     # 0.1%
    
    # NSE Market Hours (IST)
    MARKET_OPEN_TIME = "09:15"
    MARKET_CLOSE_TIME = "15:30"
    MARKET_TIMEZONE = "Asia/Kolkata"
    
    # Supported Exchanges
    SUPPORTED_EXCHANGES = ['NSE']  # Focus on NSE only for production
    
    # Hammer Pattern Detection Settings
    HAMMER_DETECTION = {
        'min_lower_shadow_ratio': 1.5,  # Lower shadow >= 1.5x body
        'max_upper_shadow_ratio': 1.0,  # Upper shadow <= 1.0x body  
        'min_body_to_range_ratio': 0.1, # Body >= 10% of total range
        'min_confidence_threshold': 70.0 # Only patterns with 70%+ confidence
    }
    
    INVERTED_HAMMER_DETECTION = {
        'min_upper_shadow_ratio': 1.5,  # Upper shadow >= 1.5x body
        'max_lower_shadow_ratio': 1.0,  # Lower shadow <= 1.0x body
        'min_body_to_range_ratio': 0.1, # Body >= 10% of total range 
        'min_confidence_threshold': 70.0 # Only patterns with 70%+ confidence
    }
    
    # Backtesting Constraints
    MAX_HOLDING_PERIOD_MINUTES = 45  # Maximum 45 minutes for intraday
    MAX_CANDLES_TO_HOLD = 3          # Maximum 3 candles (15-min timeframe)
    MIN_STOCKS_FOR_ANALYSIS = 1
    MAX_STOCKS_FOR_ANALYSIS = 50
    
    # Data Validation
    MIN_DATA_POINTS = 10  # Minimum candles required for analysis
    MAX_MISSING_DATA_PERCENTAGE = 20  # Max 20% missing data allowed
    
    # Cache Settings (for production optimization)
    CACHE_EXPIRY_MINUTES = 15  # Cache instrument data for 15 minutes
    ENABLE_DATA_CACHING = True
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Error Handling
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # 1 second
    
    # Production Security
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    # Angel One Specific Settings
    ANGEL_BASE_URL = "https://apiconnect.angelbroking.com"
    ANGEL_API_VERSION = "v1"
    
    # Instrument Master File URL
    INSTRUMENTS_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    # Historical Data Settings
    SUPPORTED_INTERVALS = {
        '1min': 'ONE_MINUTE',
        '3min': 'THREE_MINUTE', 
        '5min': 'FIVE_MINUTE',
        '10min': 'TEN_MINUTE',
        '15min': 'FIFTEEN_MINUTE',  # Primary timeframe
        '30min': 'THIRTY_MINUTE',
        '1hour': 'ONE_HOUR',
        '1day': 'ONE_DAY'
    }
    
    DEFAULT_TIMEFRAME = '15min'
    
    # Data Quality Checks
    QUALITY_CHECKS = {
        'check_missing_ohlc': True,
        'check_invalid_prices': True, 
        'check_zero_volume': True,
        'check_price_gaps': True,
        'max_price_gap_percentage': 10.0  # Alert if price gap > 10%
    }
    
    @classmethod
    def get_angel_headers(cls):
        """Get standard headers for Angel One API requests"""
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': '192.168.1.1',
            'X-ClientPublicIP': '106.193.147.98',
            'X-MACAddress': 'fe:3a:59:a9:3a:13',
            'X-PrivateKey': cls.ANGEL_ONE_API_KEY
        }
    
    @classmethod
    def is_production(cls):
        """Check if running in production environment"""
        return not cls.DEBUG
    
    @classmethod 
    def validate_config(cls):
        """Validate all configuration settings"""
        errors = []
        
        # Check Angel One credentials
        try:
            cls.validate_angel_credentials()
        except ValueError as e:
            errors.append(str(e))
        
        # Check numeric values
        if cls.MAX_HOLDING_PERIOD_MINUTES <= 0:
            errors.append("MAX_HOLDING_PERIOD_MINUTES must be positive")
        
        if cls.MAX_CANDLES_TO_HOLD <= 0:
            errors.append("MAX_CANDLES_TO_HOLD must be positive")
        
        if cls.MIN_STOCKS_FOR_ANALYSIS < 1:
            errors.append("MIN_STOCKS_FOR_ANALYSIS must be at least 1")
        
        if cls.MAX_STOCKS_FOR_ANALYSIS > 100:
            errors.append("MAX_STOCKS_FOR_ANALYSIS should not exceed 100")
        
        if errors:
            raise ValueError(f"Configuration errors: {errors}")
        
        return True

# Global configuration instance
config = Config()

# Validate configuration on import (only in production)
if config.is_production():
    try:
        config.validate_config()
    except ValueError as e:
        raise RuntimeError(f"Invalid production configuration: {e}")