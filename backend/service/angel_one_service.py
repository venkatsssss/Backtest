import asyncio
import pandas as pd
import logging
import pyotp
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from SmartApi import SmartConnect
from backend.config import Config
logger = logging.getLogger(__name__)

class AngelOneService:
    """Angel One SmartAPI integration"""
    
    def __init__(self):
        self.api_key = Config.ANGEL_ONE_API_KEY
        self.client_id = Config.ANGEL_ONE_CLIENT_ID
        self.password = Config.ANGEL_ONE_PASSWORD
        self.totp_secret = Config.ANGEL_ONE_TOTP_SECRET
        
        self.smart_api = None
        self.auth_token = None
        self.feed_token = None
        self.is_authenticated = False
        self.instruments_cache = {}
        
    async def authenticate(self) -> bool:
        """Authenticate with Angel One API"""
        try:
            if not Config.validate_credentials():
                logger.warning("Missing Angel One credentials")
                return False
            
            # Initialize SmartConnect
            self.smart_api = SmartConnect(api_key=self.api_key)
            
            # Generate TOTP
            totp = pyotp.TOTP(self.totp_secret).now()
            
            # Generate session
            data = self.smart_api.generateSession(
                self.client_id,
                self.password,
                totp
            )
            
            if data['status'] == False:
                logger.error(f"Authentication failed: {data}")
                return False
            
            self.auth_token = data['data']['jwtToken']
            self.feed_token = self.smart_api.getfeedToken()
            self.is_authenticated = True
            
            logger.info("✅ Angel One authentication successful")
            
            # Load instruments
            await self.load_instruments()
            
            return True
            
        except Exception as e:
            logger.error(f"Angel One authentication error: {e}")
            return False
    
    async def load_instruments(self) -> bool:
        """Load NSE instruments master data"""
        try:
            response = requests.get(Config.INSTRUMENTS_URL, timeout=30)
            
            if response.status_code != 200:
                logger.error("Failed to download instruments")
                return False
            
            instruments_data = response.json()
            
            # Filter NSE equity instruments
            nse_instruments = []
            for instrument in instruments_data:
                try:
                    if (instrument.get('exch_seg') == 'NSE' and 
                        instrument.get('symbol', '').endswith('-EQ')):
                        
                        clean_symbol = instrument['symbol'].replace('-EQ', '')
                        nse_instruments.append({
                            'symbol': clean_symbol,
                            'name': instrument.get('name', clean_symbol),
                            'token': instrument.get('token', ''),
                            'exchange': 'NSE',
                            'sector': self._classify_sector(clean_symbol)
                        })
                except Exception:
                    continue
            
            self.instruments_cache = {s['symbol']: s for s in nse_instruments}
            logger.info(f"✅ Loaded {len(nse_instruments)} NSE instruments")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading instruments: {e}")
            return False
    
    def _classify_sector(self, symbol: str) -> str:
        """Basic sector classification"""
        sector_keywords = {
            'banking': ['SBIN', 'HDFCBANK', 'ICICIBANK', 'AXISBANK', 'KOTAKBANK', 'INDUSINDBK'],
            'it': ['TCS', 'INFY', 'WIPRO', 'HCLTECH', 'TECHM', 'LTIM'],
            'fmcg': ['ITC', 'HINDUNILVR', 'NESTLEIND', 'BRITANNIA', 'DABUR'],
            'pharma': ['SUNPHARMA', 'DRREDDY', 'CIPLA', 'DIVISLAB', 'AUROPHARMA'],
            'auto': ['MARUTI', 'TATAMOTORS', 'M&M', 'BAJAJ-AUTO', 'EICHERMOT'],
            'oil_gas': ['RELIANCE', 'ONGC', 'BPCL', 'IOC', 'GAIL']
        }
        
        for sector, stocks in sector_keywords.items():
            if symbol.upper() in stocks:
                return sector
        
        return 'general'
    
    async def get_nse_stocks(self, sector: str = "all") -> List[Dict]:
        """Get NSE stocks list, optionally filtered by sector"""
        try:
            if not self.instruments_cache:
                await self.load_instruments()
            
            stocks = list(self.instruments_cache.values())
            
            if sector != "all":
                stocks = [s for s in stocks if s.get('sector') == sector]
            
            return stocks
            
        except Exception as e:
            logger.error(f"Error getting stocks: {e}")
            return []
    
    async def get_historical_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str,
        interval: str = 'FIFTEEN_MINUTE'
    ) -> pd.DataFrame:
        """
        Get historical OHLC data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'SBIN')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            interval: Candle interval (default: FIFTEEN_MINUTE)
        
        Returns:
            DataFrame with OHLC data
        """
        try:
            if not self.is_authenticated:
                logger.error("Not authenticated with Angel One")
                return pd.DataFrame()
            
            # Get token for symbol
            instrument = self.instruments_cache.get(symbol)
            if not instrument:
                logger.error(f"Symbol {symbol} not found in instruments")
                return pd.DataFrame()
            
            token = instrument['token']
            
            # Format dates for API
            from_date = datetime.strptime(start_date, '%Y-%m-%d')
            to_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            from_date_str = from_date.strftime('%Y-%m-%d') + ' 09:15'
            to_date_str = to_date.strftime('%Y-%m-%d') + ' 15:30'
            
            # Prepare request
            historic_param = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": interval,
                "fromdate": from_date_str,
                "todate": to_date_str
            }
            
            # Get historical data
            response = self.smart_api.getCandleData(historic_param)
            
            if not response or response.get('status') == False:
                logger.error(f"Failed to get data for {symbol}: {response}")
                return pd.DataFrame()
            
            # Parse data
            data = response.get('data', [])
            if not data:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Create DataFrame
            df = pd.DataFrame(
                data,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Process DataFrame
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Ensure timezone
            if df.index.tz is None:
                df.index = df.index.tz_localize('Asia/Kolkata')
            
            # Convert to numeric
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Remove any NaN rows
            df = df.dropna()
            
            logger.info(f"✅ Retrieved {len(df)} candles for {symbol}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
    
    async def get_multiple_historical_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        interval: str = 'FIFTEEN_MINUTE'
    ) -> Dict[str, pd.DataFrame]:
        """Get historical data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            try:
                df = await self.get_historical_data(symbol, start_date, end_date, interval)
                if not df.empty:
                    results[symbol] = df
                
                # Rate limiting - wait between requests
                await asyncio.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        return results
    
    def logout(self):
        """Logout from Angel One"""
        try:
            if self.smart_api and self.client_id:
                self.smart_api.terminateSession(self.client_id)
                logger.info("Logged out from Angel One")
        except Exception as e:
            logger.error(f"Logout error: {e}")