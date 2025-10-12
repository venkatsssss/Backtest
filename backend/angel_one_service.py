"""
Fallback Angel One implementation without smartapi-python dependency
Direct API calls using requests library only
"""

import asyncio
import pandas as pd
import numpy as np
import logging
import pyotp
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class AngelOneFallbackService:
    """Direct Angel One API implementation without external dependencies"""
    
    def __init__(self):
        self.api_key = os.getenv('ANGEL_ONE_API_KEY')
        self.client_id = os.getenv('ANGEL_ONE_CLIENT_ID')
        self.password = os.getenv('ANGEL_ONE_PASSWORD')
        self.totp_secret = os.getenv('ANGEL_ONE_TOTP_SECRET')
        
        self.base_url = "https://apiconnect.angelbroking.com"
        self.auth_token = None
        self.is_authenticated = False
        self.instruments_cache = {}
        
    async def authenticate(self) -> bool:
        """Authenticate using direct API calls"""
        try:
            if not all([self.api_key, self.client_id, self.password]):
                logger.warning("Missing Angel One credentials, using demo mode")
                return False
            
            # Generate TOTP
            totp = None
            if self.totp_secret:
                totp = pyotp.TOTP(self.totp_secret).now()
            
            # Authentication payload
            auth_payload = {
                "clientcode": self.client_id,
                "password": self.password,
                "totp": totp
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': '192.168.1.1',
                'X-ClientPublicIP': '106.193.147.98',
                'X-MACAddress': 'fe:3a:59:a9:3a:13',
                'X-PrivateKey': self.api_key
            }
            
            # Make authentication request
            response = requests.post(
                f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword",
                headers=headers,
                json=auth_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status'):
                    self.auth_token = data['data']['jwtToken']
                    self.is_authenticated = True
                    logger.info("Successfully authenticated with Angel One")
                    await self.load_instruments()
                    return True
            
            logger.warning("Angel One authentication failed, using demo mode")
            return False
            
        except Exception as e:
            logger.error(f"Angel One authentication error: {e}")
            return False

    async def load_instruments(self) -> bool:
        """Load NSE instruments from Angel One"""
        try:
            # Download instruments master file
            instruments_url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
            response = requests.get(instruments_url, timeout=30)
            
            if response.status_code == 200:
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
                                'sector': self._classify_sector(clean_symbol),
                                'is_active': True
                            })
                    except Exception:
                        continue
                
                self.instruments_cache = {'NSE': nse_instruments}
                logger.info(f"Loaded {len(nse_instruments)} NSE instruments")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error loading instruments: {e}")
            return False

    def _classify_sector(self, symbol: str) -> str:
        """Basic sector classification"""
        sector_map = {
            'TCS': 'it', 'INFY': 'it', 'WIPRO': 'it', 'HCLTECH': 'it',
            'SBIN': 'banking', 'HDFCBANK': 'banking', 'ICICIBANK': 'banking',
            'RELIANCE': 'oil_gas', 'ONGC': 'oil_gas', 'BPCL': 'oil_gas',
            'ITC': 'fmcg', 'HINDUNILVR': 'fmcg', 'NESTLEIND': 'fmcg',
            'ASIANPAINT': 'consumer', 'MARUTI': 'consumer', 'TITAN': 'consumer'
        }
        return sector_map.get(symbol.upper(), 'general')

    async def get_nse_stocks(self, sector: str = "all") -> List[Dict]:
        """Get NSE stocks filtered by sector"""
        try:
            if 'NSE' not in self.instruments_cache:
                # Use demo data if no instruments loaded
                return self._get_demo_stocks(sector)
            
            instruments = self.instruments_cache['NSE']
            
            if sector != "all":
                instruments = [
                    stock for stock in instruments 
                    if stock.get('sector', '').lower() == sector.lower()
                ]
            
            return instruments
            
        except Exception as e:
            logger.error(f"Error getting NSE stocks: {e}")
            return self._get_demo_stocks(sector)

    async def get_historical_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical data - falls back to demo if API fails"""
        try:
            if not self.is_authenticated:
                return self._generate_demo_data(symbol, start_date, end_date)
            
            # Get token for symbol
            token = self._get_token_for_symbol(symbol)
            if not token:
                return self._generate_demo_data(symbol, start_date, end_date)
            
            # Prepare historical data request
            from_date = datetime.strptime(start_date, '%Y-%m-%d')
            to_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            payload = {
                "exchange": "NSE",
                "symboltoken": token,
                "interval": "FIFTEEN_MINUTE",
                "fromdate": from_date.strftime('%Y-%m-%d 09:15'),
                "todate": to_date.strftime('%Y-%m-%d 15:30')
            }
            
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': '192.168.1.1',
                'X-ClientPublicIP': '106.193.147.98',
                'X-MACAddress': 'fe:3a:59:a9:3a:13',
                'X-PrivateKey': self.api_key
            }
            
            # Make API request
            response = requests.post(
                f"{self.base_url}/rest/secure/angelbroking/historical/v1/getCandleData",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    # Convert to DataFrame
                    df = pd.DataFrame(
                        data['data'],
                        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    )
                    
                    # Process data
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df.set_index('timestamp', inplace=True)
                    df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
                    
                    # Convert to numeric
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    df = df.dropna()
                    logger.info(f"Retrieved {len(df)} candles for {symbol}")
                    return df
            
            # Fallback to demo data
            return self._generate_demo_data(symbol, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return self._generate_demo_data(symbol, start_date, end_date)

    def _get_token_for_symbol(self, symbol: str) -> Optional[str]:
        """Get token for symbol"""
        instruments = self.instruments_cache.get('NSE', [])
        for instrument in instruments:
            if instrument['symbol'] == symbol:
                return instrument['token']
        return None

    def _get_demo_stocks(self, sector: str) -> List[Dict]:
        """Get demo stocks for testing"""
        demo_stocks = [
            {"symbol": "TCS", "name": "Tata Consultancy Services", "sector": "it", "exchange": "NSE", "is_active": True, "token": "11536"},
            {"symbol": "RELIANCE", "name": "Reliance Industries", "sector": "oil_gas", "exchange": "NSE", "is_active": True, "token": "2885"},
            {"symbol": "HDFCBANK", "name": "HDFC Bank", "sector": "banking", "exchange": "NSE", "is_active": True, "token": "1333"},
            {"symbol": "INFY", "name": "Infosys", "sector": "it", "exchange": "NSE", "is_active": True, "token": "1594"},
            {"symbol": "ICICIBANK", "name": "ICICI Bank", "sector": "banking", "exchange": "NSE", "is_active": True, "token": "4963"},
            {"symbol": "SBIN", "name": "State Bank of India", "sector": "banking", "exchange": "NSE", "is_active": True, "token": "3045"},
            {"symbol": "ITC", "name": "ITC Limited", "sector": "fmcg", "exchange": "NSE", "is_active": True, "token": "1660"},
            {"symbol": "ASIANPAINT", "name": "Asian Paints", "sector": "consumer", "exchange": "NSE", "is_active": True, "token": "236"},
            {"symbol": "MARUTI", "name": "Maruti Suzuki", "sector": "auto", "exchange": "NSE", "is_active": True, "token": "10999"},
            {"symbol": "TITAN", "name": "Titan Company", "sector": "consumer", "exchange": "NSE", "is_active": True, "token": "3506"}
        ]
        
        if sector != "all":
            demo_stocks = [s for s in demo_stocks if s["sector"] == sector]
        
        return demo_stocks

    def _generate_demo_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate realistic demo data"""
        try:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            
            # Generate timestamps for business days, 15-minute intervals
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
            
            # Base prices for different stocks
            base_prices = {
                'SBIN': 820, 'TCS': 3500, 'RELIANCE': 2800, 
                'HDFCBANK': 1600, 'INFY': 1800, 'ITC': 450,
                'ASIANPAINT': 3200, 'MARUTI': 11000, 'TITAN': 3400
            }
            base_price = base_prices.get(symbol, 1000)
            
            # Generate realistic OHLC data with patterns
            data = []
            current_price = base_price
            
            for timestamp in timestamps:
                # Add market volatility
                volatility = np.random.normal(0, 0.015)
                open_price = current_price
                close_price = open_price * (1 + volatility)
                
                # Generate high/low
                high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
                low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
                
                # Create hammer patterns (5% chance)
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
            logger.error(f"Error generating demo data: {e}")
            return pd.DataFrame()

    async def get_multiple_historical_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """Get historical data for multiple symbols"""
        results = {}
        
        for symbol in symbols:
            try:
                data = await self.get_historical_data(symbol, start_date, end_date)
                if not data.empty:
                    results[symbol] = data
                await asyncio.sleep(0.2)  # Rate limiting
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        return results