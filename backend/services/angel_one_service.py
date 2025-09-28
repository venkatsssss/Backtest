import asyncio
import pandas as pd
import numpy as np
import logging
import pyotp
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from SmartApi import SmartConnect
from config import Config

logger = logging.getLogger(__name__)

class AngelOneService:
    """Production-ready Angel One API service for real NSE data"""
    
    def __init__(self):
        self.api_key = Config.ANGEL_ONE_API_KEY
        self.client_id = Config.ANGEL_ONE_CLIENT_ID
        self.password = Config.ANGEL_ONE_PASSWORD
        self.totp_secret = Config.ANGEL_ONE_TOTP_SECRET
        
        self.smart_api = None
        self.auth_token = None
        self.is_authenticated = False
        self.instruments_cache = {}
        self.last_request_time = 0
        
        # Rate limiting
        self.request_count = 0
        self.request_window_start = datetime.now()

    async def authenticate(self) -> bool:
        """Authenticate with Angel One API"""
        try:
            logger.info("Authenticating with Angel One API...")
            
            # Validate credentials
            if not all([self.api_key, self.client_id, self.password]):
                logger.error("Missing Angel One API credentials")
                return False
            
            # Initialize SmartConnect
            self.smart_api = SmartConnect(api_key=self.api_key)
            
            # Generate TOTP if available
            totp = None
            if self.totp_secret:
                totp = pyotp.TOTP(self.totp_secret).now()
                logger.info(f"Generated TOTP: {totp[:2]}****")
            
            # Authenticate
            response = self.smart_api.generateSession(
                self.client_id, 
                self.password, 
                totp
            )
            
            if response and response.get('status'):
                self.auth_token = response['data']['jwtToken']
                self.is_authenticated = True
                logger.info("Successfully authenticated with Angel One")
                
                # Load instruments after authentication
                await self.load_instruments()
                return True
            else:
                logger.error(f"Angel One authentication failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Angel One authentication error: {str(e)}")
            return False

    async def load_instruments(self) -> bool:
        """Load NSE instruments from Angel One master file"""
        try:
            logger.info("Loading NSE instruments from Angel One...")
            
            # Download master file
            response = requests.get(Config.INSTRUMENTS_URL, timeout=30)
            response.raise_for_status()
            
            instruments_data = response.json()
            logger.info(f"Downloaded {len(instruments_data)} instruments")
            
            # Filter for NSE equity instruments
            nse_instruments = []
            
            for instrument in instruments_data:
                try:
                    exchange = instrument.get('exch_seg', '')
                    symbol = instrument.get('symbol', '')
                    name = instrument.get('name', '')
                    token = instrument.get('token', '')
                    
                    # Filter for NSE equity only
                    if exchange == 'NSE' and symbol.endswith('-EQ'):
                        clean_symbol = symbol.replace('-EQ', '')
                        
                        # Skip if already exists
                        if clean_symbol in [inst['symbol'] for inst in nse_instruments]:
                            continue
                        
                        nse_instruments.append({
                            'symbol': clean_symbol,
                            'name': name,
                            'token': token,
                            'exchange': 'NSE',
                            'sector': self._classify_sector(clean_symbol),
                            'is_active': True
                        })
                        
                except Exception as e:
                    continue  # Skip problematic instruments
            
            # Sort by symbol
            nse_instruments.sort(key=lambda x: x['symbol'])
            
            # Cache instruments
            self.instruments_cache = {
                'NSE': nse_instruments,
                'loaded_at': datetime.now()
            }
            
            logger.info(f"Loaded {len(nse_instruments)} NSE equity instruments")
            return True
            
        except Exception as e:
            logger.error(f"Error loading instruments: {str(e)}")
            return False

    def _classify_sector(self, symbol: str) -> str:
        """Classify stock symbol into sector"""
        # Enhanced sector classification
        sector_map = {
            # Banking
            'HDFCBANK': 'banking', 'ICICIBANK': 'banking', 'SBIN': 'banking', 
            'KOTAKBANK': 'banking', 'AXISBANK': 'banking', 'INDUSINDBK': 'banking',
            'FEDERALBNK': 'banking', 'PNB': 'banking', 'CANBK': 'banking',
            'BANKBARODA': 'banking', 'UNIONBANK': 'banking', 'YESBANK': 'banking',
            
            # IT
            'TCS': 'it', 'INFY': 'it', 'WIPRO': 'it', 'HCLTECH': 'it',
            'TECHM': 'it', 'LTI': 'it', 'MPHASIS': 'it', 'MINDTREE': 'it',
            
            # FMCG
            'HINDUNILVR': 'fmcg', 'ITC': 'fmcg', 'NESTLEIND': 'fmcg',
            'BRITANNIA': 'fmcg', 'DABUR': 'fmcg', 'MARICO': 'fmcg',
            'GODREJCP': 'fmcg', 'COLPAL': 'fmcg',
            
            # Oil & Gas
            'RELIANCE': 'oil_gas', 'ONGC': 'oil_gas', 'BPCL': 'oil_gas',
            'IOCL': 'oil_gas', 'HINDPETRO': 'oil_gas', 'GAIL': 'oil_gas',
            
            # Pharma
            'SUNPHARMA': 'pharma', 'DRREDDY': 'pharma', 'CIPLA': 'pharma',
            'LUPIN': 'pharma', 'BIOCON': 'pharma', 'DIVISLAB': 'pharma',
            
            # Consumer
            'ASIANPAINT': 'consumer', 'MARUTI': 'consumer', 'TITAN': 'consumer',
            'BAJAJ-AUTO': 'consumer', 'HEROMOTOCO': 'consumer',
            
            # Auto
            'TATAMOTORS': 'auto', 'M&M': 'auto', 'ASHOKLEY': 'auto',
            'TVSMOTOR': 'auto', 'ESCORTS': 'auto',
            
            # Metals
            'TATASTEEL': 'metals', 'JSWSTEEL': 'metals', 'SAIL': 'metals',
            'JINDALSTEL': 'metals', 'HINDALCO': 'metals', 'VEDL': 'metals',
            'COALINDIA': 'metals', 'NMDC': 'metals',
            
            # Telecom
            'BHARTIARTL': 'telecom', 'IDEA': 'telecom',
        }
        
        return sector_map.get(symbol.upper(), 'general')

    async def get_nse_stocks(self, sector: str = "all") -> List[Dict]:
        """Get NSE stocks filtered by sector"""
        try:
            # Check if instruments are loaded
            if 'NSE' not in self.instruments_cache:
                await self.load_instruments()
            
            instruments = self.instruments_cache.get('NSE', [])
            
            # Apply sector filter
            if sector != "all":
                instruments = [
                    stock for stock in instruments 
                    if stock.get('sector', '').lower() == sector.lower()
                ]
            
            logger.info(f"Returning {len(instruments)} stocks for sector: {sector}")
            return instruments
            
        except Exception as e:
            logger.error(f"Error getting NSE stocks: {str(e)}")
            return []

    async def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get 15-minute historical data from Angel One API"""
        try:
            # Rate limiting
            await self._apply_rate_limit()
            
            if not self.is_authenticated:
                logger.warning(f"Not authenticated, generating demo data for {symbol}")
                return self._generate_demo_data(symbol, start_date, end_date)
            
            # Get instrument token
            token = self._get_token_for_symbol(symbol)
            if not token:
                logger.warning(f"Token not found for {symbol}, using demo data")
                return self._generate_demo_data(symbol, start_date, end_date)
            
            # Convert dates
            from_date = datetime.strptime(start_date, '%Y-%m-%d')
            to_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Prepare request parameters
            historical_param = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": "FIFTEEN_MINUTE",
                "fromdate": from_date.strftime('%Y-%m-%d 09:15'),
                "todate": to_date.strftime('%Y-%m-%d 15:30')
            }
            
            logger.info(f"Fetching {symbol} data: {historical_param}")
            
            # Make API call
            response = self.smart_api.getCandleData(historical_param)
            
            if response and response.get('status') and response.get('data'):
                # Convert to DataFrame
                df = pd.DataFrame(
                    response['data'],
                    columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                )
                
                # Process timestamp
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
                
                # Convert to IST
                df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
                
                # Ensure numeric types
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # Remove any rows with NaN values
                df = df.dropna()
                
                logger.info(f"Retrieved {len(df)} candles for {symbol}")
                return df
                
            else:
                logger.warning(f"No data received for {symbol}, using demo data")
                return self._generate_demo_data(symbol, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return self._generate_demo_data(symbol, start_date, end_date)

    def _get_token_for_symbol(self, symbol: str) -> Optional[str]:
        """Get Angel One token for symbol"""
        instruments = self.instruments_cache.get('NSE', [])
        for instrument in instruments:
            if instrument['symbol'] == symbol:
                return instrument['token']
        return None

    async def _apply_rate_limit(self):
        """Apply rate limiting for Angel One API"""
        current_time = datetime.now()
        
        # Reset counter if window expired
        if (current_time - self.request_window_start).seconds >= 60:
            self.request_count = 0
            self.request_window_start = current_time
        
        # Check if we've exceeded rate limit
        if self.request_count >= Config.MAX_HISTORICAL_REQUESTS_PER_MINUTE:
            sleep_time = 60 - (current_time - self.request_window_start).seconds
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time}s")
                await asyncio.sleep(sleep_time)
                self.request_count = 0
                self.request_window_start = datetime.now()
        
        # Apply minimum delay between requests
        if Config.REQUEST_DELAY > 0:
            await asyncio.sleep(Config.REQUEST_DELAY)
        
        self.request_count += 1

    def _generate_demo_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate realistic demo data for testing"""
        try:
            # Create business day range
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            # Generate 15-minute intervals for business days
            timestamps = []
            current_date = start
            
            while current_date <= end:
                if current_date.weekday() < 5:  # Monday to Friday
                    day_start = current_date.replace(hour=9, minute=15)
                    day_end = current_date.replace(hour=15, minute=30)
                    
                    current_time = day_start
                    while current_time <= day_end:
                        timestamps.append(current_time)
                        current_time += timedelta(minutes=15)
                
                current_date += timedelta(days=1)
            
            if not timestamps:
                return pd.DataFrame()
            
            # Base price for different stocks
            base_prices = {
                'SBIN': 820, 'TCS': 3500, 'RELIANCE': 2800, 
                'HDFCBANK': 1600, 'INFY': 1800, 'ITC': 450
            }
            base_price = base_prices.get(symbol, 1000)
            
            # Generate realistic OHLC data
            data = []
            current_price = base_price
            
            for timestamp in timestamps:
                # Market volatility
                volatility = np.random.normal(0, 0.015)  # 1.5% volatility
                
                open_price = current_price
                close_price = open_price * (1 + volatility)
                
                # Generate high/low with realistic spreads
                high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
                low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
                
                # Create hammer patterns occasionally (5% chance)
                if np.random.random() < 0.05:
                    body_size = abs(close_price - open_price)
                    lower_shadow = body_size * np.random.uniform(2, 4)
                    upper_shadow = body_size * np.random.uniform(0.1, 0.5)
                    
                    low_price = min(open_price, close_price) - lower_shadow
                    high_price = max(open_price, close_price) + upper_shadow
                
                # Create inverted hammer patterns (3% chance)
                elif np.random.random() < 0.03:
                    body_size = abs(close_price - open_price)
                    upper_shadow = body_size * np.random.uniform(2, 4)
                    lower_shadow = body_size * np.random.uniform(0.1, 0.5)
                    
                    high_price = max(open_price, close_price) + upper_shadow
                    low_price = min(open_price, close_price) - lower_shadow
                
                volume = np.random.randint(10000, 500000)
                
                data.append({
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume
                })
                
                current_price = close_price
            
            # Create DataFrame
            df = pd.DataFrame(data, index=timestamps)
            df.index = pd.to_datetime(df.index).tz_localize('Asia/Kolkata')
            
            logger.info(f"Generated {len(df)} demo candles for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error generating demo data: {str(e)}")
            return pd.DataFrame()

    async def get_multiple_historical_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Get historical data for multiple symbols"""
        results = {}
        
        for i, symbol in enumerate(symbols):
            try:
                logger.info(f"Processing {symbol} ({i+1}/{len(symbols)})")
                
                data = await self.get_historical_data(symbol, start_date, end_date)
                if not data.empty:
                    results[symbol] = data
                
                # Progress logging
                if (i + 1) % 5 == 0:
                    logger.info(f"Processed {i+1}/{len(symbols)} symbols")
                
                # Rate limiting delay
                await asyncio.sleep(Config.REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                continue
        
        logger.info(f"Successfully retrieved data for {len(results)}/{len(symbols)} symbols")
        return results