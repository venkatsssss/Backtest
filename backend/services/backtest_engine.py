
import pandas as pd
import numpy as np
import logging
import asyncio
from datetime import datetime, time
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Production-ready backtesting engine for hammer patterns"""
    
    def __init__(self):
        self.hammer_config = Config.HAMMER_DETECTION
        self.inverted_hammer_config = Config.INVERTED_HAMMER_DETECTION
        self.market_open = time(9, 15)
        self.market_close = time(15, 30)

    async def run_hammer_analysis(self, stocks: List[str], strategy: str, 
                                 target_percent: float, stop_loss_percent: float,
                                 start_date: str, end_date: str, 
                                 angel_service) -> Dict:
        """Run comprehensive hammer pattern analysis"""
        
        logger.info(f"Starting {strategy} analysis for {len(stocks)} stocks")
        
        # Initialize results
        detailed_trades = []
        stock_results = []
        
        # Counters
        total_profit = 0
        total_safe = 0
        total_stop_loss = 0
        total_no_returns = 0
        
        # Process each stock
        for i, stock in enumerate(stocks):
            try:
                logger.info(f"Processing {stock} ({i+1}/{len(stocks)})")
                
                # Get historical data
                historical_data = await angel_service.get_historical_data(
                    stock, start_date, end_date
                )
                
                if historical_data.empty:
                    logger.warning(f"No data available for {stock}")
                    continue
                
                # Validate data quality
                if not self._validate_data_quality(historical_data, stock):
                    continue
                
                logger.info(f"Analyzing {len(historical_data)} candles for {stock}")
                
                # Detect patterns
                patterns = self.detect_patterns(historical_data, strategy)
                
                if not patterns:
                    logger.info(f"No {strategy} patterns found for {stock}")
                    continue
                
                logger.info(f"Found {len(patterns)} {strategy} patterns for {stock}")
                
                # Test each pattern
                stock_profit = 0
                stock_safe = 0 
                stock_stop_loss = 0
                stock_no_returns = 0
                
                for pattern in patterns:
                    outcome = await self.test_pattern_outcome(
                        pattern, historical_data, target_percent, stop_loss_percent
                    )
                    
                    # Create detailed trade record
                    trade_detail = self._create_trade_record(
                        stock, pattern, outcome, target_percent, stop_loss_percent
                    )
                    detailed_trades.append(trade_detail)
                    
                    # Count outcomes
                    if outcome['outcome'] == 'profit':
                        stock_profit += 1
                        total_profit += 1
                    elif outcome['outcome'] == 'safe':
                        stock_safe += 1
                        total_safe += 1
                    elif outcome['outcome'] == 'stop_loss':
                        stock_stop_loss += 1
                        total_stop_loss += 1
                    else:
                        stock_no_returns += 1
                        total_no_returns += 1
                
                # Stock summary
                total_patterns_for_stock = len(patterns)
                profit_rate = (stock_profit / total_patterns_for_stock * 100) if total_patterns_for_stock > 0 else 0
                
                stock_results.append({
                    'symbol': stock,
                    'patterns_found': total_patterns_for_stock,
                    'profit_count': stock_profit,
                    'safe_count': stock_safe,
                    'stop_loss_count': stock_stop_loss,
                    'no_returns_count': stock_no_returns,
                    'profit_rate': round(profit_rate, 2)
                })
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing {stock}: {str(e)}")
                continue
        
        # Calculate overall results
        total_patterns = total_profit + total_safe + total_stop_loss + total_no_returns
        
        if total_patterns == 0:
            return self._create_empty_result(strategy, start_date, end_date, target_percent, stop_loss_percent)
        
        # Calculate rates
        profit_rate = round((total_profit / total_patterns) * 100, 2)
        safe_rate = round((total_safe / total_patterns) * 100, 2)
        stop_loss_rate = round((total_stop_loss / total_patterns) * 100, 2)
        no_returns_rate = round((total_no_returns / total_patterns) * 100, 2)
        
        # Sort results
        detailed_trades.sort(key=lambda x: x['timestamp'], reverse=True)
        stock_results.sort(key=lambda x: x['profit_rate'], reverse=True)
        
        logger.info(f"Analysis complete: {total_patterns} patterns, {len(detailed_trades)} trades")
        
        return {
            'profit_rate': profit_rate,
            'safe_rate': safe_rate,
            'stop_loss_rate': stop_loss_rate,
            'no_returns_rate': no_returns_rate,
            'total_patterns': total_patterns,
            'strategy': strategy.replace('_', ' ').title(),
            'period': f"{start_date} to {end_date}",
            'stocks_analyzed': len([s for s in stock_results if s['patterns_found'] > 0]),
            'target_percent': target_percent,
            'stop_loss_percent': stop_loss_percent,
            'stock_results': stock_results[:25],  # Top 25 stocks
            'detailed_trades': detailed_trades,
            'timeframe': '15-minute intraday',
            'data_source': 'Angel One API' if angel_service.is_authenticated else 'Demo Data'
        }

    def detect_patterns(self, df: pd.DataFrame, pattern_type: str) -> List[Dict]:
        """Detect hammer or inverted hammer patterns"""
        
        if df.empty:
            return []
        
        patterns = []
        
        for i in range(len(df)):
            try:
                row = df.iloc[i]
                timestamp = df.index[i]
                
                # Get OHLC values
                open_val = float(row['open'])
                high_val = float(row['high'])
                low_val = float(row['low'])
                close_val = float(row['close'])
                
                # Detect pattern
                is_pattern = False
                confidence = 0.0
                
                if pattern_type == "hammer":
                    is_pattern, confidence = self._is_hammer_pattern(
                        open_val, high_val, low_val, close_val
                    )
                elif pattern_type == "inverted_hammer":
                    is_pattern, confidence = self._is_inverted_hammer_pattern(
                        open_val, high_val, low_val, close_val
                    )
                
                # Only include high-confidence patterns
                if is_pattern and confidence >= Config.HAMMER_DETECTION['min_confidence_threshold']:
                    pattern = {
                        'timestamp': timestamp,
                        'open': open_val,
                        'high': high_val,
                        'low': low_val,
                        'close': close_val,
                        'pattern_type': pattern_type,
                        'entry_price': close_val,
                        'confidence': round(confidence, 1)
                    }
                    patterns.append(pattern)
                    
            except Exception as e:
                continue
        
        return patterns

    def _is_hammer_pattern(self, open_price: float, high_price: float, 
                          low_price: float, close_price: float) -> tuple:
        """Detect hammer pattern with confidence score"""
        
        try:
            if high_price <= low_price:
                return False, 0.0
            
            # Calculate components
            body = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range <= 0 or body <= 0:
                return False, 0.0
            
            # Ratios
            lower_shadow_ratio = lower_shadow / body
            upper_shadow_ratio = upper_shadow / body
            body_to_range_ratio = body / total_range
            
            # Hammer criteria (production-grade)
            conditions = [
                lower_shadow_ratio >= self.hammer_config['min_lower_shadow_ratio'],
                upper_shadow_ratio <= self.hammer_config['max_upper_shadow_ratio'],
                body_to_range_ratio >= self.hammer_config['min_body_to_range_ratio'],
                lower_shadow > upper_shadow,  # Lower shadow must be longer
                total_range > 0.01  # Meaningful price movement
            ]
            
            if not all(conditions):
                return False, 0.0
            
            # Calculate confidence score
            confidence = self._calculate_hammer_confidence(
                lower_shadow_ratio, upper_shadow_ratio, body_to_range_ratio
            )
            
            return True, confidence
            
        except Exception:
            return False, 0.0

    def _is_inverted_hammer_pattern(self, open_price: float, high_price: float,
                                   low_price: float, close_price: float) -> tuple:
        """Detect inverted hammer pattern with confidence score"""
        
        try:
            if high_price <= low_price:
                return False, 0.0
            
            # Calculate components
            body = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range <= 0 or body <= 0:
                return False, 0.0
            
            # Ratios
            upper_shadow_ratio = upper_shadow / body
            lower_shadow_ratio = lower_shadow / body
            body_to_range_ratio = body / total_range
            
            # Inverted hammer criteria
            conditions = [
                upper_shadow_ratio >= self.inverted_hammer_config['min_upper_shadow_ratio'],
                lower_shadow_ratio <= self.inverted_hammer_config['max_lower_shadow_ratio'],
                body_to_range_ratio >= self.inverted_hammer_config['min_body_to_range_ratio'],
                upper_shadow > lower_shadow,  # Upper shadow must be longer
                total_range > 0.01  # Meaningful price movement
            ]
            
            if not all(conditions):
                return False, 0.0
            
            # Calculate confidence score
            confidence = self._calculate_inverted_hammer_confidence(
                upper_shadow_ratio, lower_shadow_ratio, body_to_range_ratio
            )
            
            return True, confidence
            
        except Exception:
            return False, 0.0

    def _calculate_hammer_confidence(self, lower_shadow_ratio: float,
                                   upper_shadow_ratio: float, 
                                   body_to_range_ratio: float) -> float:
        """Calculate confidence score for hammer pattern"""
        
        # Base score
        confidence = 50.0
        
        # Lower shadow dominance (max +30 points)
        if lower_shadow_ratio >= 3.0:
            confidence += 30
        elif lower_shadow_ratio >= 2.0:
            confidence += 20
        else:
            confidence += 10
        
        # Upper shadow minimality (max +15 points)
        if upper_shadow_ratio <= 0.5:
            confidence += 15
        elif upper_shadow_ratio <= 1.0:
            confidence += 10
        else:
            confidence += 5
        
        # Body significance (max +5 points)
        if body_to_range_ratio >= 0.2:
            confidence += 5
        
        return min(confidence, 100.0)

    def _calculate_inverted_hammer_confidence(self, upper_shadow_ratio: float,
                                            lower_shadow_ratio: float,
                                            body_to_range_ratio: float) -> float:
        """Calculate confidence score for inverted hammer pattern"""
        
        # Base score
        confidence = 50.0
        
        # Upper shadow dominance (max +30 points)
        if upper_shadow_ratio >= 3.0:
            confidence += 30
        elif upper_shadow_ratio >= 2.0:
            confidence += 20
        else:
            confidence += 10
        
        # Lower shadow minimality (max +15 points)
        if lower_shadow_ratio <= 0.5:
            confidence += 15
        elif lower_shadow_ratio <= 1.0:
            confidence += 10
        else:
            confidence += 5
        
        # Body significance (max +5 points)
        if body_to_range_ratio >= 0.2:
            confidence += 5
        
        return min(confidence, 100.0)

    async def test_pattern_outcome(self, pattern: Dict, df: pd.DataFrame,
                                  target_percent: float, stop_loss_percent: float) -> Dict:
        """Test pattern outcome with intraday constraints"""
        
        entry_price = pattern['entry_price']
        entry_time = pattern['timestamp']
        
        target_price = entry_price * (1 + target_percent / 100)
        stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
        
        try:
            # Get future data after pattern
            future_data = df[df.index > entry_time].copy()
            
            if future_data.empty:
                return self._create_no_data_outcome(entry_price, entry_time)
            
            # Apply intraday constraints
            same_day_candles = self._get_same_day_candles(future_data, entry_time)
            
            if not same_day_candles:
                return self._create_no_data_outcome(entry_price, entry_time)
            
            # Test outcomes within constraints
            for candle_num, (timestamp, row) in enumerate(same_day_candles, 1):
                try:
                    minutes_held = candle_num * 15  # 15-minute intervals
                    
                    high_price = float(row['high'])
                    low_price = float(row['low'])
                    close_price = float(row['close'])
                    
                    # Check target hit first (higher priority)
                    if high_price >= target_price:
                        return {
                            'outcome': 'profit',
                            'exit_price': target_price,
                            'exit_time': timestamp,
                            'minutes_held': minutes_held,
                            'candles_held': candle_num,
                            'exit_reason': f'Target achieved in {minutes_held} minutes'
                        }
                    
                    # Check stop loss
                    if low_price <= stop_loss_price:
                        return {
                            'outcome': 'stop_loss',
                            'exit_price': stop_loss_price,
                            'exit_time': timestamp,
                            'minutes_held': minutes_held,
                            'candles_held': candle_num,
                            'exit_reason': f'Stop loss triggered in {minutes_held} minutes'
                        }
                        
                except Exception:
                    continue
            
            # Forced exit after maximum holding period
            final_timestamp, final_row = same_day_candles[-1]
            final_price = float(final_row['close'])
            final_minutes = len(same_day_candles) * 15
            
            outcome = 'safe' if final_price > entry_price else 'no_returns'
            
            return {
                'outcome': outcome,
                'exit_price': final_price,
                'exit_time': final_timestamp,
                'minutes_held': final_minutes,
                'candles_held': len(same_day_candles),
                'exit_reason': f'Forced exit after {final_minutes} minutes'
            }
            
        except Exception as e:
            logger.error(f"Error in outcome testing: {e}")
            return self._create_no_data_outcome(entry_price, entry_time)

    def _get_same_day_candles(self, future_data: pd.DataFrame, entry_time) -> List:
        """Get candles for same trading day with constraints"""
        
        same_day_candles = []
        entry_date = entry_time.date()
        
        for timestamp, row in future_data.iterrows():
            # Check if same trading day
            if timestamp.date() != entry_date:
                break
            
            # Check market hours
            if not (self.market_open <= timestamp.time() <= self.market_close):
                continue
            
            # Maximum holding period constraint
            if len(same_day_candles) >= Config.MAX_CANDLES_TO_HOLD:
                break
            
            same_day_candles.append((timestamp, row))
        
        return same_day_candles

    def _create_trade_record(self, stock: str, pattern: Dict, outcome: Dict,
                           target_percent: float, stop_loss_percent: float) -> Dict:
        """Create detailed trade record"""
        
        entry_price = pattern['entry_price']
        exit_price = outcome.get('exit_price', entry_price)
        
        return {
            'stock': stock,
            'timestamp': pattern['timestamp'].isoformat(),
            'pattern_time': pattern['timestamp'].strftime('%d-%b %H:%M'),
            'exit_time_formatted': outcome.get('exit_time', pattern['timestamp']).strftime('%d-%b %H:%M'),
            'pattern_type': pattern['pattern_type'].replace('_', ' ').title(),
            'entry_price': round(entry_price, 2),
            'exit_price': round(exit_price, 2),
            'target_price': round(entry_price * (1 + target_percent / 100), 2),
            'stop_loss_price': round(entry_price * (1 - stop_loss_percent / 100), 2),
            'outcome': outcome['outcome'],
            'points_gained': round(exit_price - entry_price, 2),
            'percentage_gain': round(((exit_price - entry_price) / entry_price) * 100, 2),
            'minutes_held': min(outcome.get('minutes_held', 0), Config.MAX_HOLDING_PERIOD_MINUTES),
            'candles_held': min(outcome.get('candles_held', 1), Config.MAX_CANDLES_TO_HOLD),
            'confidence': pattern.get('confidence', 0.0),
            'exit_reason': outcome.get('exit_reason', 'Unknown')
        }

    def _create_no_data_outcome(self, entry_price: float, entry_time) -> Dict:
        """Create outcome for no data scenarios"""
        return {
            'outcome': 'no_returns',
            'exit_price': entry_price,
            'exit_time': entry_time,
            'minutes_held': 0,
            'candles_held': 0,
            'exit_reason': 'Insufficient future data'
        }

    def _create_empty_result(self, strategy: str, start_date: str, end_date: str,
                           target_percent: float, stop_loss_percent: float) -> Dict:
        """Create empty result when no patterns found"""
        return {
            'profit_rate': 0.0,
            'safe_rate': 0.0,
            'stop_loss_rate': 0.0,
            'no_returns_rate': 0.0,
            'total_patterns': 0,
            'strategy': strategy.replace('_', ' ').title(),
            'period': f"{start_date} to {end_date}",
            'stocks_analyzed': 0,
            'target_percent': target_percent,
            'stop_loss_percent': stop_loss_percent,
            'stock_results': [],
            'detailed_trades': [],
            'timeframe': '15-minute intraday',
            'message': f'No {strategy.replace("_", " ")} patterns detected in the selected period'
        }

    def _validate_data_quality(self, df: pd.DataFrame, symbol: str) -> bool:
        """Validate data quality before analysis"""
        
        try:
            # Check minimum data points
            if len(df) < Config.MIN_DATA_POINTS:
                logger.warning(f"Insufficient data for {symbol}: {len(df)} candles")
                return False
            
            # Check for missing OHLC values
            required_cols = ['open', 'high', 'low', 'close']
            for col in required_cols:
                if col not in df.columns:
                    logger.error(f"Missing {col} column for {symbol}")
                    return False
                
                null_count = df[col].isnull().sum()
                null_percentage = (null_count / len(df)) * 100
                
                if null_percentage > Config.MAX_MISSING_DATA_PERCENTAGE:
                    logger.warning(f"Too many null values in {col} for {symbol}: {null_percentage:.1f}%")
                    return False
            
            # Check for invalid price relationships
            invalid_count = 0
            for idx, row in df.iterrows():
                try:
                    o, h, l, c = row['open'], row['high'], row['low'], row['close']
                    
                    # Basic OHLC validation
                    if not (l <= o <= h and l <= c <= h and l <= h):
                        invalid_count += 1
                        
                except Exception:
                    invalid_count += 1
            
            invalid_percentage = (invalid_count / len(df)) * 100
            if invalid_percentage > Config.MAX_MISSING_DATA_PERCENTAGE:
                logger.warning(f"Too many invalid OHLC relationships for {symbol}: {invalid_percentage:.1f}%")
                return False
            
            # Check for zero/negative prices
            price_cols = ['open', 'high', 'low', 'close']
            for col in price_cols:
                if (df[col] <= 0).any():
                    logger.warning(f"Zero or negative prices found in {col} for {symbol}")
                    return False
            
            logger.info(f"Data quality validation passed for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Data validation error for {symbol}: {e}")
            return False