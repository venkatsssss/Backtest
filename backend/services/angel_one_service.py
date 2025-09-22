# Real Angel One API Integration - REAL DATA ONLY, NO FAKE/DEMO DATA

import asyncio
import pandas as pd
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
import logging
from SmartApi import SmartConnect
import pyotp
import os
import requests
from dotenv import load_dotenv
import numpy as np

load_dotenv()

logger = logging.getLogger(__name__)

class RealAngelOneService:
    def __init__(self):
        self.api_key = os.getenv('ANGEL_ONE_API_KEY')
        self.client_id = os.getenv('ANGEL_ONE_CLIENT_ID')
        self.password = os.getenv('ANGEL_ONE_PASSWORD')
        self.totp_secret = os.getenv('ANGEL_ONE_TOTP_SECRET')
        self.smart_api = None
        self.auth_token = None
        self.is_authenticated = False
        self.instruments_cache = None
        
        # Indian market holidays (2024-2025)
        self.market_holidays = {
            '2024-01-26', '2024-03-08', '2024-03-25', '2024-03-29', '2024-04-11',
            '2024-04-17', '2024-05-01', '2024-06-17', '2024-08-15', '2024-08-19',
            '2024-10-02', '2024-10-31', '2024-11-01', '2024-11-15',
            '2025-01-26', '2025-03-14', '2025-04-10', '2025-04-14', '2025-04-18',
            '2025-05-01', '2025-06-06', '2025-08-15', '2025-09-07', '2025-10-02',
            '2025-10-20', '2025-11-04'
        }

    def is_trading_day(self, date: datetime) -> bool:
        """Check if given date is a trading day (not weekend or holiday)"""
        if date.weekday() >= 5:  # Weekend
            return False
        date_str = date.strftime('%Y-%m-%d')
        return date_str not in self.market_holidays

    def is_trading_time(self, dt: datetime) -> bool:
        """Check if given datetime is within trading hours (9:15 AM - 3:30 PM IST)"""
        if not self.is_trading_day(dt):
            return False
        current_time = dt.time()
        market_open = time(9, 15)
        market_close = time(15, 30)
        return market_open <= current_time <= market_close

    async def authenticate(self):
        """Authenticate with Angel One API - REQUIRED for real data"""
        if not all([self.api_key, self.client_id, self.password]):
            logger.error("❌ Missing Angel One credentials. Please set API_KEY, CLIENT_ID, PASSWORD in .env file")
            return False
            
        try:
            self.smart_api = SmartConnect(api_key=self.api_key)
            
            # Generate TOTP if available
            totp = None
            if self.totp_secret:
                totp = pyotp.TOTP(self.totp_secret).now()
                logger.info("🔐 Generated TOTP for authentication")
            else:
                logger.warning("⚠️ No TOTP secret provided. Authentication may fail.")
            
            # Generate session
            logger.info("🔄 Attempting Angel One authentication...")
            data = self.smart_api.generateSession(
                self.client_id,
                self.password,
                totp
            )
            
            if data and data.get('status'):
                self.auth_token = data['data']['jwtToken']
                self.is_authenticated = True
                logger.info("✅ Angel One authentication successful!")
                await self.load_instruments()
                return True
            else:
                logger.error(f"❌ Angel One authentication failed: {data}")
                self.is_authenticated = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Angel One authentication error: {str(e)}")
            self.is_authenticated = False
            return False

    async def load_instruments(self):
        """Load real NSE instruments from Angel One API"""
        if not self.is_authenticated:
            logger.error("❌ Cannot load instruments - not authenticated")
            return []

        try:
            logger.info("📡 Fetching real instruments from Angel One API...")
            url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ Failed to fetch instruments: HTTP {response.status_code}")
                return []
                
            instruments_data = response.json()
            logger.info(f"📊 Received {len(instruments_data)} instruments from Angel One")

            equity_instruments = []
            for instrument in instruments_data:
                exch_seg = instrument.get('exch_seg', '')
                symbol = instrument.get('symbol', '')
                
                if exch_seg == 'NSE' and symbol.endswith('-EQ'):
                    symbol_clean = symbol.replace('-EQ', '')
                    equity_instruments.append({
                        'symbol': symbol_clean,
                        'name': instrument.get('name', symbol_clean),
                        'token': instrument['token'],
                        'exchange': 'NSE',
                        'sector': self._get_sector_from_symbol(symbol_clean),
                        'is_active': True
                    })

            self.instruments_cache = equity_instruments
            logger.info(f"✅ Loaded {len(self.instruments_cache)} real NSE equity instruments")
            return self.instruments_cache

        except Exception as e:
            logger.error(f"❌ Error loading real instruments: {str(e)}")
            return []

    def _get_sector_from_symbol(self, symbol):
        """Map symbol to sector"""
        symbol = symbol.upper()
        sector_mapping = {
            # Banking
            'HDFCBANK': 'banking', 'ICICIBANK': 'banking', 'SBIN': 'banking', 'KOTAKBANK': 'banking',
            'AXISBANK': 'banking', 'INDUSINDBK': 'banking', 'PNB': 'banking',
            
            # IT
            'TCS': 'it', 'INFY': 'it', 'WIPRO': 'it', 'HCLTECH': 'it', 'TECHM': 'it',
            
            # FMCG
            'HINDUNILVR': 'fmcg', 'ITC': 'fmcg', 'NESTLEIND': 'fmcg', 'BRITANNIA': 'fmcg',
            
            # Oil & Gas
            'RELIANCE': 'oil_gas', 'ONGC': 'oil_gas', 'BPCL': 'oil_gas', 'IOCL': 'oil_gas',
            
            # Pharma
            'SUNPHARMA': 'pharma', 'DRREDDY': 'pharma', 'CIPLA': 'pharma', 'LUPIN': 'pharma',
            
            # Consumer
            'ASIANPAINT': 'consumer', 'MARUTI': 'consumer', 'TITAN': 'consumer',
            
            # Others
            'TATASTEEL': 'metals', 'JSWSTEEL': 'metals', 'COALINDIA': 'metals',
            'BHARTIARTL': 'telecom', 'NTPC': 'power', 'POWERGRID': 'power',
            'ADANIPORTS': 'infrastructure', 'LT': 'infrastructure'
        }
        return sector_mapping.get(symbol, 'general')

    async def get_nse_stocks(self, sector: str = "all") -> List[Dict]:
        """Get real NSE stocks - AUTHENTICATION REQUIRED"""
        if not self.is_authenticated:
            logger.error("❌ Cannot get stocks - Angel One API not authenticated")
            logger.error("❌ Please ensure your Angel One credentials are correct in .env file")
            return []

        if not self.instruments_cache:
            logger.warning("⚠️ No instruments cache, loading from API...")
            await self.load_instruments()

        if not self.instruments_cache:
            logger.error("❌ Failed to load real instruments from Angel One API")
            return []

        stocks = self.instruments_cache
        
        if sector != "all":
            stocks = [s for s in stocks if s.get('sector', '').lower() == sector.lower()]

        logger.info(f"✅ Returning {len(stocks)} REAL stocks from Angel One API for sector: {sector}")
        return sorted(stocks, key=lambda x: x['symbol'])

    def get_token(self, symbol: str) -> Optional[str]:
        """Get real token for symbol from Angel One instruments"""
        if not self.instruments_cache:
            logger.error("❌ No instruments cache available")
            return None
        
        for instrument in self.instruments_cache:
            if instrument['symbol'] == symbol:
                return instrument['token']
        
        logger.warning(f"⚠️ Token not found for symbol: {symbol}")
        return None

    async def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get REAL historical data from Angel One API - NO FAKE DATA"""
        
        # STRICT CHECK: Must be authenticated
        if not self.is_authenticated:
            logger.error(f"❌ Cannot get data for {symbol} - Angel One API not authenticated")
            logger.error("❌ Please authenticate first using valid credentials")
            return pd.DataFrame()  # Return empty DataFrame - NO FAKE DATA
        
        # STRICT CHECK: Validate trading days
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Check if date range has trading days
        trading_days = []
        current_date = start_dt
        while current_date <= end_dt:
            if self.is_trading_day(current_date):
                trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        if not trading_days:
            logger.warning(f"⚠️ No trading days in range {start_date} to {end_date} for {symbol}")
            return pd.DataFrame()  # Return empty - NO FAKE DATA
        
        # Get real token
        token = self.get_token(symbol)
        if not token:
            logger.error(f"❌ No token found for {symbol} in real Angel One data")
            return pd.DataFrame()  # Return empty - NO FAKE DATA
        
        try:
            logger.info(f"📡 Fetching REAL 15-minute data for {symbol} from Angel One API")
            
            # Prepare API request
            historical_param = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": "FIFTEEN_MINUTE",
                "fromdate": start_dt.strftime('%Y-%m-%d 09:15'),
                "todate": end_dt.strftime('%Y-%m-%d 15:30')
            }
            
            logger.info(f"📊 API Request: {historical_param}")
            
            # Make REAL API call
            historical_data = self.smart_api.getCandleData(historical_param)
            
            # STRICT validation of API response
            if not historical_data:
                logger.error(f"❌ No response from Angel One API for {symbol}")
                return pd.DataFrame()
            
            if not historical_data.get('status', False):
                logger.error(f"❌ Angel One API returned error for {symbol}: {historical_data}")
                return pd.DataFrame()
            
            if not historical_data.get('data'):
                logger.warning(f"⚠️ No historical data available from Angel One for {symbol}")
                return pd.DataFrame()
            
            # Process REAL data
            df = pd.DataFrame(
                historical_data['data'],
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            if df.empty:
                logger.warning(f"⚠️ Empty dataset received from Angel One for {symbol}")
                return pd.DataFrame()
            
            # Convert timestamps properly
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any invalid data
            df = df.dropna()
            
            # STRICT: Only include trading hours data
            df = df[df.index.map(self.is_trading_time)]
            
            if df.empty:
                logger.warning(f"⚠️ No valid trading hours data for {symbol}")
                return pd.DataFrame()
            
            logger.info(f"✅ Retrieved {len(df)} REAL 15-minute candles for {symbol}")
            logger.info(f"   Date range: {df.index.min()} to {df.index.max()}")
            
            # Log sample data for verification
            if len(df) > 0:
                sample = df.head(2)
                for idx, row in sample.iterrows():
                    logger.info(f"   Sample: {idx} -> O:{row['open']:.2f} H:{row['high']:.2f} L:{row['low']:.2f} C:{row['close']:.2f}")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Error fetching REAL data for {symbol}: {str(e)}")
            return pd.DataFrame()  # Return empty - NO FAKE DATA

    async def get_multiple_historical_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Get real historical data for multiple symbols - AUTHENTICATION REQUIRED"""
        
        if not self.is_authenticated:
            logger.error("❌ Cannot get historical data - Angel One API not authenticated")
            return {}  # Return empty - NO FAKE DATA
        
        results = {}
        successful_count = 0
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"📊 Processing {symbol} ({i+1}/{len(symbols)})")
                
                data = await self.get_historical_data(symbol, start_date, end_date)
                
                if not data.empty:
                    results[symbol] = data
                    successful_count += 1
                    logger.info(f"✅ Got REAL data for {symbol}: {len(data)} candles")
                else:
                    logger.warning(f"⚠️ No REAL data available for {symbol}")
                
                # Respect API rate limits
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"❌ Error getting REAL data for {symbol}: {str(e)}")
                continue
        
        logger.info(f"✅ Successfully retrieved REAL data for {successful_count}/{len(symbols)} symbols")
        
        if successful_count == 0:
            logger.error("❌ No real data retrieved for any symbol. Check Angel One API connection and authentication.")
        
        return results

    def detect_hammer_patterns(self, df: pd.DataFrame, pattern_type: str) -> List[Dict]:
        """Strict hammer pattern detection on REAL data only"""
        
        if df.empty:
            logger.warning("❌ No data available for pattern detection")
            return []
        
        # Verify this is real data (not demo)
        logger.info(f"🔍 REAL DATA PATTERN DETECTION:")
        logger.info(f"   Total candles: {len(df)}")
        logger.info(f"   Date range: {df.index.min()} to {df.index.max()}")
        logger.info(f"   Pattern: {pattern_type}")
        
        patterns = []
        
        for i in range(len(df)):
            try:
                row = df.iloc[i]
                timestamp = df.index[i]
                
                # Ensure trading hours only
                if not self.is_trading_time(timestamp.to_pydatetime()):
                    continue
                
                open_val = float(row['open'])
                high_val = float(row['high'])
                low_val = float(row['low'])
                close_val = float(row['close'])
                
                # Strict pattern detection
                is_pattern = False
                confidence = 0.0
                
                if pattern_type == "hammer":
                    is_pattern, confidence = self._strict_hammer_test(open_val, high_val, low_val, close_val)
                elif pattern_type == "inverted_hammer":
                    is_pattern, confidence = self._strict_inverted_hammer_test(open_val, high_val, low_val, close_val)
                
                # Only high-confidence patterns (80%+)
                if is_pattern and confidence >= 80.0:
                    pattern = {
                        'timestamp': timestamp,
                        'open': open_val,
                        'high': high_val,
                        'low': low_val,
                        'close': close_val,
                        'pattern_type': pattern_type,
                        'entry_price': close_val,
                        'confidence': confidence,
                        'data_source': 'Angel One Real API'
                    }
                    patterns.append(pattern)
                    logger.info(f"🔨 REAL {pattern_type.upper()} at {timestamp}: "
                               f"O={open_val:.2f} H={high_val:.2f} L={low_val:.2f} C={close_val:.2f} "
                               f"(Confidence: {confidence:.1f}%)")
                    
            except Exception as e:
                continue
        
        logger.info(f"✅ Found {len(patterns)} high-confidence {pattern_type} patterns in REAL data")
        return patterns

    def _strict_hammer_test(self, open_price: float, high_price: float, low_price: float, close_price: float) -> tuple:
        """Very strict hammer pattern test"""
        try:
            if high_price <= low_price:
                return False, 0.0
            
            body = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range <= 0 or lower_shadow <= 0:
                return False, 0.0
            
            # Very strict conditions
            effective_body = max(body, total_range * 0.1)  # Handle small bodies
            lower_body_ratio = lower_shadow / effective_body
            upper_body_ratio = upper_shadow / effective_body
            lower_dominance = lower_shadow / total_range
            
            # Strict criteria
            if (lower_body_ratio >= 3.0 and           # Lower shadow at least 3x body
                upper_body_ratio <= 0.3 and          # Upper shadow max 30% of body
                lower_dominance >= 0.65):             # Lower shadow at least 65% of range
                
                confidence = min(100, 50 + (lower_body_ratio * 10) + (lower_dominance * 30))
                return True, confidence
            
            return False, 0.0
            
        except Exception:
            return False, 0.0

    def _strict_inverted_hammer_test(self, open_price: float, high_price: float, low_price: float, close_price: float) -> tuple:
        """Very strict inverted hammer pattern test"""
        try:
            if high_price <= low_price:
                return False, 0.0
            
            body = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range <= 0 or upper_shadow <= 0:
                return False, 0.0
            
            # Very strict conditions
            effective_body = max(body, total_range * 0.1)
            upper_body_ratio = upper_shadow / effective_body
            lower_body_ratio = lower_shadow / effective_body
            upper_dominance = upper_shadow / total_range
            
            # Strict criteria
            if (upper_body_ratio >= 3.0 and           # Upper shadow at least 3x body
                lower_body_ratio <= 0.3 and          # Lower shadow max 30% of body
                upper_dominance >= 0.65):             # Upper shadow at least 65% of range
                
                confidence = min(100, 50 + (upper_body_ratio * 10) + (upper_dominance * 30))
                return True, confidence
            
            return False, 0.0
            
        except Exception:
            return False, 0.0

# Global instance
angel_one_service = RealAngelOneService()
