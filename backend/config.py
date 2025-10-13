import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application Configuration"""
    
    # Angel One API Credentials
    ANGEL_ONE_API_KEY = os.getenv('ANGEL_ONE_API_KEY')
    ANGEL_ONE_CLIENT_ID = os.getenv('ANGEL_ONE_CLIENT_ID')
    ANGEL_ONE_PASSWORD = os.getenv('ANGEL_ONE_PASSWORD')
    ANGEL_ONE_TOTP_SECRET = os.getenv('ANGEL_ONE_TOTP_SECRET')
    
    # Server Settings
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # CORS
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
    
    # Market Settings
    MARKET_OPEN_TIME = "09:15"
    MARKET_CLOSE_TIME = "15:30"
    MARKET_TIMEZONE = "Asia/Kolkata"
    
    # Hammer Pattern Detection Criteria
    HAMMER_MIN_LOWER_SHADOW_RATIO = 2.0  # Lower shadow >= 2x body
    HAMMER_MAX_UPPER_SHADOW_RATIO = 0.5  # Upper shadow <= 0.5x body
    HAMMER_MIN_BODY_RATIO = 0.1  # Body >= 10% of total range
    
    # Inverted Hammer Pattern Detection Criteria
    INV_HAMMER_MIN_UPPER_SHADOW_RATIO = 2.0  # Upper shadow >= 2x body
    INV_HAMMER_MAX_LOWER_SHADOW_RATIO = 0.5  # Lower shadow <= 0.5x body
    INV_HAMMER_MIN_BODY_RATIO = 0.1  # Body >= 10% of total range
    
    # Trading Constraints (Intraday)
    MAX_HOLDING_MINUTES = 390  # Full trading day (6.5 hours)
    
    # API Settings
    INSTRUMENTS_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    
    # Timeframe intervals
    TIMEFRAME_MAP = {
        '1min': 'ONE_MINUTE',
        '5min': 'FIVE_MINUTE',
        '10min': 'TEN_MINUTE',
        '15min': 'FIFTEEN_MINUTE',
        '30min': 'THIRTY_MINUTE',
        '1hour': 'ONE_HOUR',
        '1day': 'ONE_DAY'
    }
    
    DEFAULT_TIMEFRAME = 'FIFTEEN_MINUTE'
    
    @classmethod
    def validate_credentials(cls):
        """Validate Angel One credentials"""
        required = [
            cls.ANGEL_ONE_API_KEY,
            cls.ANGEL_ONE_CLIENT_ID,
            cls.ANGEL_ONE_PASSWORD,
            cls.ANGEL_ONE_TOTP_SECRET
        ]
        return all(required)

config = Config()