# Real Data Only Backtest Engine - NO FAKE/DEMO DATA

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta, time
import asyncio

logger = logging.getLogger(__name__)

class RealDataBacktestEngine:
    def __init__(self):
        # Market validation
        self.market_open = time(9, 15)
        self.market_close = time(15, 30)
        
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
        """Check if given date is a trading day"""
        if date.weekday() >= 5:  # Weekend
            return False
        return date.strftime('%Y-%m-%d') not in self.market_holidays

    def is_trading_time(self, dt: datetime) -> bool:
        """Check if datetime is within trading hours"""
        if not self.is_trading_day(dt):
            return False
        return self.market_open <= dt.time() <= self.market_close

    async def run_hammer_analysis(self, stocks: List[str], strategy: str,
                                 target_percent: float, stop_loss_percent: float,
                                 start_date: str, end_date: str) -> Dict:
        
        logger.info(f"🚀 Starting REAL DATA ONLY {strategy} analysis for {len(stocks)} stocks")
        
        # Import Angel One service
        from .angel_one_service import angel_one_service
        
        # STRICT CHECK: Ensure Angel One is authenticated
        if not angel_one_service.is_authenticated:
            logger.error("❌ Angel One API not authenticated - cannot proceed with real data analysis")
            return {
                'profit_rate': 0.0, 'safe_rate': 0.0, 'stop_loss_rate': 0.0, 'no_returns_rate': 0.0,
                'total_patterns': 0, 'strategy': str(strategy).replace('_', ' ').title(),
                'period': f"{start_date} to {end_date}", 'stocks_analyzed': 0,
                'target_percent': float(target_percent), 'stop_loss_percent': float(stop_loss_percent),
                'stock_results': [], 'detailed_trades': [],
                'error': 'Angel One API not authenticated. Please check your credentials.',
                'timeframe': 'Real Data Required'
            }
        
        # Validate date range has trading days
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        trading_days = []
        current_date = start_dt
        while current_date <= end_dt:
            if self.is_trading_day(current_date):
                trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        if not trading_days:
            logger.warning(f"⚠️ No trading days in range {start_date} to {end_date}")
            return {
                'profit_rate': 0.0, 'safe_rate': 0.0, 'stop_loss_rate': 0.0, 'no_returns_rate': 0.0,
                'total_patterns': 0, 'strategy': str(strategy).replace('_', ' ').title(),
                'period': f"{start_date} to {end_date}", 'stocks_analyzed': 0,
                'target_percent': float(target_percent), 'stop_loss_percent': float(stop_loss_percent),
                'stock_results': [], 'detailed_trades': [],
                'message': f'No trading days in selected period (contains only weekends/holidays)',
                'timeframe': 'Real Data Only'
            }
        
        logger.info(f"📅 Analyzing {len(trading_days)} trading days")
        
        # Initialize counters
        detailed_trades = []
        stock_results = []
        total_profit = 0
        total_safe = 0
        total_stop_loss = 0
        total_no_returns = 0
        stocks_with_data = 0
        
        for i, stock in enumerate(stocks):
            try:
                logger.info(f"📊 Processing {stock} ({i+1}/{len(stocks)}) - REAL DATA ONLY")
                
                # Get REAL historical data from Angel One API
                historical_data = await angel_one_service.get_historical_data(
                    stock, start_date, end_date
                )
                
                if historical_data.empty:
                    logger.warning(f"⚠️ No REAL data available from Angel One API for {stock}")
                    continue
                
                # Verify data is from trading hours only
                valid_data = historical_data[historical_data.index.map(self.is_trading_time)]
                if valid_data.empty:
                    logger.warning(f"⚠️ No valid trading hours data for {stock}")
                    continue
                
                stocks_with_data += 1
                logger.info(f"✅ Processing {len(valid_data)} REAL candles for {stock}")
                
                # Detect patterns using REAL data
                patterns = await self._detect_real_patterns(valid_data, strategy, stock)
                
                if not patterns:
                    logger.info(f"   No high-confidence {strategy} patterns found in REAL data for {stock}")
                    continue
                
                logger.info(f"🔨 Found {len(patterns)} high-confidence REAL {strategy} patterns for {stock}")
                
                # Test each pattern outcome
                profit_count = 0
                safe_count = 0
                stop_loss_count = 0
                no_returns_count = 0
                
                for pattern in patterns:
                    outcome = await self._test_real_pattern_outcome(
                        pattern, valid_data, target_percent, stop_loss_percent
                    )
                    
                    # Create detailed trade record
                    trade_detail = {
                        'stock': str(stock),
                        'timestamp': str(pattern['timestamp']),
                        'pattern_time': pattern['timestamp'].strftime('%d-%b-%Y %H:%M') if hasattr(pattern['timestamp'], 'strftime') else str(pattern['timestamp']),
                        'exit_time_formatted': outcome.get('exit_time_formatted', 'N/A'),
                        'pattern_type': str(pattern['pattern_type']).replace('_', ' ').title(),
                        'entry_price': round(float(pattern['entry_price']), 2),
                        'exit_price': round(float(outcome.get('exit_price', pattern['entry_price'])), 2),
                        'target_price': round(float(outcome.get('target_price', 0)), 2),
                        'stop_loss_price': round(float(outcome.get('stop_loss_price', 0)), 2),
                        'outcome': str(outcome['outcome']),
                        'points_gained': round(float(outcome.get('exit_price', pattern['entry_price'])) - float(pattern['entry_price']), 2),
                        'percentage_gain': round(((float(outcome.get('exit_price', pattern['entry_price'])) - float(pattern['entry_price'])) / float(pattern['entry_price'])) * 100, 2),
                        'minutes_held': int(outcome.get('minutes_held', 0)),
                        'candles_held': int(outcome.get('candles_held', 0)),
                        'confidence': round(float(pattern.get('confidence', 0)), 1),
                        'exit_reason': str(outcome.get('exit_reason', 'Unknown')),
                        'data_source': 'Angel One Real API'
                    }
                    
                    detailed_trades.append(trade_detail)
                    
                    # Count outcomes
                    if outcome['outcome'] == 'profit':
                        profit_count += 1
                    elif outcome['outcome'] == 'safe':
                        safe_count += 1
                    elif outcome['outcome'] == 'stop_loss':
                        stop_loss_count += 1
                    else:
                        no_returns_count += 1
                
                # Stock-level results
                total_patterns_for_stock = len(patterns)
                profit_rate = (profit_count / total_patterns_for_stock * 100) if total_patterns_for_stock > 0 else 0
                
                stock_results.append({
                    'symbol': str(stock),
                    'patterns_found': int(total_patterns_for_stock),
                    'profit_count': int(profit_count),
                    'safe_count': int(safe_count),
                    'stop_loss_count': int(stop_loss_count),
                    'no_returns_count': int(no_returns_count),
                    'profit_rate': round(float(profit_rate), 2),
                    'avg_confidence': round(float(np.mean([p['confidence'] for p in patterns])), 1) if patterns else 0,
                    'data_source': 'Angel One Real API'
                })
                
                # Update totals
                total_profit += profit_count
                total_safe += safe_count
                total_stop_loss += stop_loss_count
                total_no_returns += no_returns_count
                
                # Respect API rate limits
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"❌ Error processing {stock}: {str(e)}")
                continue
        
        # Final results
        total_patterns = total_profit + total_safe + total_stop_loss + total_no_returns
        
        if total_patterns == 0:
            logger.warning(f"⚠️ No high-confidence patterns found in REAL data across {len(stocks)} stocks")
            return {
                'profit_rate': 0.0, 'safe_rate': 0.0, 'stop_loss_rate': 0.0, 'no_returns_rate': 0.0,
                'total_patterns': 0, 'strategy': str(strategy).replace('_', ' ').title(),
                'period': f"{start_date} to {end_date}", 'stocks_analyzed': stocks_with_data,
                'target_percent': float(target_percent), 'stop_loss_percent': float(stop_loss_percent),
                'stock_results': [], 'detailed_trades': [],
                'message': f'No high-confidence {str(strategy).replace("_", " ")} patterns detected with minimum 85% confidence',
                'timeframe': 'Real Data Only', 'data_source': 'Angel One API',
                'trading_days_analyzed': len(trading_days)
            }
        
        # Calculate success rates
        profit_rate = round((total_profit / total_patterns) * 100, 2)
        safe_rate = round((total_safe / total_patterns) * 100, 2)
        stop_loss_rate = round((total_stop_loss / total_patterns) * 100, 2)
        no_returns_rate = round((total_no_returns / total_patterns) * 100, 2)
        
        # Sort results by performance
        detailed_trades.sort(key=lambda x: (x['timestamp'], -x['confidence']), reverse=True)
        stock_results.sort(key=lambda x: (x['profit_rate'], x['avg_confidence']), reverse=True)
        
        logger.info(f"✅ REAL DATA Analysis Complete:")
        logger.info(f"   Total patterns: {total_patterns}")
        logger.info(f"   Profit rate: {profit_rate}%")
        logger.info(f"   Stocks analyzed: {stocks_with_data}")
        
        return {
            'profit_rate': float(profit_rate),
            'safe_rate': float(safe_rate),
            'stop_loss_rate': float(stop_loss_rate),
            'no_returns_rate': float(no_returns_rate),
            'total_patterns': int(total_patterns),
            'strategy': str(strategy).replace('_', ' ').title(),
            'period': f"{start_date} to {end_date}",
            'stocks_analyzed': int(stocks_with_data),
            'target_percent': float(target_percent),
            'stop_loss_percent': float(stop_loss_percent),
            'stock_results': stock_results[:15],  # Top 15 stocks
            'detailed_trades': detailed_trades[:30],  # Top 30 trades
            'timeframe': 'Real Intraday 15-minute',
            'data_source': 'Angel One API',
            'trading_days_analyzed': len(trading_days),
            'pattern_detection': 'High Confidence (85%+ only)',
            'avg_confidence': round(float(np.mean([t['confidence'] for t in detailed_trades])), 1) if detailed_trades else 0,
            'authentication_status': 'Angel One API Authenticated'
        }

    async def _detect_real_patterns(self, df: pd.DataFrame, pattern_type: str, symbol: str) -> List[Dict]:
        """Detect patterns in REAL data only - very strict criteria"""
        
        if df.empty:
            return []
        
        logger.info(f"🔍 Analyzing REAL {pattern_type} patterns for {symbol}")
        logger.info(f"   Data points: {len(df)}")
        logger.info(f"   Date range: {df.index.min()} to {df.index.max()}")
        
        patterns = []
        
        for i in range(len(df)):
            try:
                row = df.iloc[i]
                timestamp = df.index[i]
                
                # Ensure trading hours
                if not self.is_trading_time(timestamp.to_pydatetime()):
                    continue
                
                open_val = float(row['open'])
                high_val = float(row['high'])
                low_val = float(row['low'])
                close_val = float(row['close'])
                
                # Very strict pattern detection
                is_pattern, confidence, details = await self._analyze_candle_pattern(
                    open_val, high_val, low_val, close_val, pattern_type
                )
                
                # Only accept very high confidence patterns (85%+)
                if is_pattern and confidence >= 85.0:
                    pattern = {
                        'timestamp': timestamp,
                        'open': open_val,
                        'high': high_val,
                        'low': low_val,
                        'close': close_val,
                        'pattern_type': pattern_type,
                        'entry_price': close_val,
                        'confidence': confidence,
                        'details': details,
                        'symbol': symbol,
                        'data_source': 'Angel One Real API'
                    }
                    patterns.append(pattern)
                    
                    logger.info(f"🔨 HIGH-CONFIDENCE {pattern_type.upper()} for {symbol} at {timestamp}:")
                    logger.info(f"    O={open_val:.2f} H={high_val:.2f} L={low_val:.2f} C={close_val:.2f}")
                    logger.info(f"    Confidence: {confidence:.1f}% | {details}")
                    
            except Exception as e:
                continue
        
        return patterns

    async def _analyze_candle_pattern(self, open_price: float, high_price: float, 
                                    low_price: float, close_price: float, pattern_type: str) -> tuple:
        """Ultra-strict candle pattern analysis"""
        
        try:
            # Basic validations
            if high_price <= low_price or high_price <= max(open_price, close_price):
                return False, 0.0, "Invalid OHLC"
            
            # Calculate measurements
            body = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range <= 0:
                return False, 0.0, "No range"
            
            # Pattern-specific analysis
            if pattern_type == "hammer":
                return await self._analyze_hammer_strict(body, lower_shadow, upper_shadow, total_range)
            elif pattern_type == "inverted_hammer":
                return await self._analyze_inverted_hammer_strict(body, lower_shadow, upper_shadow, total_range)
            
            return False, 0.0, "Unknown pattern"
            
        except Exception as e:
            return False, 0.0, f"Analysis error: {str(e)}"

    async def _analyze_hammer_strict(self, body: float, lower_shadow: float, 
                                   upper_shadow: float, total_range: float) -> tuple:
        """Ultra-strict hammer analysis"""
        
        if lower_shadow <= 0:
            return False, 0.0, "No lower shadow"
        
        # Handle very small bodies
        effective_body = max(body, total_range * 0.08)  # Min 8% of total range
        
        # Ultra-strict criteria
        lower_body_ratio = lower_shadow / effective_body
        upper_body_ratio = upper_shadow / effective_body
        lower_dominance = lower_shadow / total_range
        
        # Requirements for high-confidence hammer
        conditions_met = 0
        confidence_points = 0
        
        # 1. Lower shadow must be at least 3x body (very strict)
        if lower_body_ratio >= 3.0:
            conditions_met += 1
            confidence_points += min(35, lower_body_ratio * 10)  # Up to 35 points
        else:
            return False, 0.0, f"Weak lower shadow ({lower_body_ratio:.1f}x)"
        
        # 2. Upper shadow must be very small (max 25% of body)
        if upper_body_ratio <= 0.25:
            conditions_met += 1
            confidence_points += 25 - (upper_body_ratio * 50)  # More points for smaller upper shadow
        else:
            return False, 0.0, f"Large upper shadow ({upper_body_ratio:.1f}x)"
        
        # 3. Lower shadow must dominate range (at least 70%)
        if lower_dominance >= 0.70:
            conditions_met += 1
            confidence_points += lower_dominance * 30  # Up to 30 points
        else:
            return False, 0.0, f"Insufficient dominance ({lower_dominance:.1%})"
        
        # 4. Meaningful range
        if total_range > 0:
            confidence_points += 10
            conditions_met += 1
        
        final_confidence = min(100, confidence_points)
        details = f"Lower={lower_body_ratio:.1f}x, Upper={upper_body_ratio:.1f}x, Dom={lower_dominance:.1%}"
        
        return True, final_confidence, details

    async def _analyze_inverted_hammer_strict(self, body: float, lower_shadow: float,
                                            upper_shadow: float, total_range: float) -> tuple:
        """Ultra-strict inverted hammer analysis"""
        
        if upper_shadow <= 0:
            return False, 0.0, "No upper shadow"
        
        effective_body = max(body, total_range * 0.08)
        
        upper_body_ratio = upper_shadow / effective_body
        lower_body_ratio = lower_shadow / effective_body
        upper_dominance = upper_shadow / total_range
        
        conditions_met = 0
        confidence_points = 0
        
        # 1. Upper shadow must be at least 3x body
        if upper_body_ratio >= 3.0:
            conditions_met += 1
            confidence_points += min(35, upper_body_ratio * 10)
        else:
            return False, 0.0, f"Weak upper shadow ({upper_body_ratio:.1f}x)"
        
        # 2. Lower shadow must be very small (max 25% of body)
        if lower_body_ratio <= 0.25:
            conditions_met += 1
            confidence_points += 25 - (lower_body_ratio * 50)
        else:
            return False, 0.0, f"Large lower shadow ({lower_body_ratio:.1f}x)"
        
        # 3. Upper shadow must dominate range (at least 70%)
        if upper_dominance >= 0.70:
            conditions_met += 1
            confidence_points += upper_dominance * 30
        else:
            return False, 0.0, f"Insufficient dominance ({upper_dominance:.1%})"
        
        # 4. Meaningful range
        if total_range > 0:
            confidence_points += 10
            conditions_met += 1
        
        final_confidence = min(100, confidence_points)
        details = f"Upper={upper_body_ratio:.1f}x, Lower={lower_body_ratio:.1f}x, Dom={upper_dominance:.1%}"
        
        return True, final_confidence, details

    async def _test_real_pattern_outcome(self, pattern: Dict, df: pd.DataFrame,
                                       target_percent: float, stop_loss_percent: float) -> Dict:
        """Test pattern outcome using REAL data with intraday constraints"""
        
        entry_price = pattern['entry_price']
        entry_time = pattern['timestamp']
        target_price = entry_price * (1 + target_percent / 100)
        stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
        
        try:
            # Get future data after pattern
            future_data = df[df.index > entry_time].copy()
            
            if future_data.empty:
                return self._create_outcome('no_returns', entry_price, entry_time, 
                                          target_price, stop_loss_price, 'No future data')
            
            # Same-day trading only, max 3 candles (45 minutes)
            entry_date = entry_time.date() if hasattr(entry_time, 'date') else str(entry_time)[:10]
            same_day_candles = []
            
            for timestamp, row in future_data.iterrows():
                candle_date = timestamp.date() if hasattr(timestamp, 'date') else str(timestamp)[:10]
                
                # Stop if different day or max candles reached
                if str(candle_date) != str(entry_date) or len(same_day_candles) >= 3:
                    break
                    
                same_day_candles.append((timestamp, row))
            
            if not same_day_candles:
                return self._create_outcome('no_returns', entry_price, entry_time,
                                          target_price, stop_loss_price, 'No same-day data')
            
            # Test each candle for target/stop-loss
            for candle_num, (timestamp, row) in enumerate(same_day_candles, 1):
                try:
                    high_price = float(row['high'])
                    low_price = float(row['low'])
                    close_price = float(row['close'])
                    minutes_held = candle_num * 15
                    
                    # Check target hit first (profit)
                    if high_price >= target_price:
                        return self._create_outcome('profit', target_price, timestamp,
                                                  target_price, stop_loss_price,
                                                  f'Target hit in candle {candle_num}',
                                                  minutes_held, candle_num)
                    
                    # Check stop loss
                    if low_price <= stop_loss_price:
                        return self._create_outcome('stop_loss', stop_loss_price, timestamp,
                                                  target_price, stop_loss_price,
                                                  f'Stop loss hit in candle {candle_num}',
                                                  minutes_held, candle_num)
                    
                except Exception as e:
                    continue
            
            # Final exit after all candles
            if same_day_candles:
                final_timestamp, final_row = same_day_candles[-1]
                final_price = float(final_row['close'])
                final_minutes = len(same_day_candles) * 15
                
                outcome = 'safe' if final_price > entry_price else 'no_returns'
                
                return self._create_outcome(outcome, final_price, final_timestamp,
                                          target_price, stop_loss_price,
                                          f'End-of-session exit after {len(same_day_candles)} candles',
                                          final_minutes, len(same_day_candles))
            
            return self._create_outcome('no_returns', entry_price, entry_time,
                                      target_price, stop_loss_price, 'No valid candles')
            
        except Exception as e:
            logger.error(f"Error testing outcome: {e}")
            return self._create_outcome('no_returns', entry_price, entry_time,
                                      target_price, stop_loss_price, 'Calculation error')

    def _create_outcome(self, outcome: str, exit_price: float, exit_time,
                       target_price: float, stop_loss_price: float, reason: str,
                       minutes_held: int = 0, candles_held: int = 0) -> Dict:
        """Create standardized outcome dictionary"""
        
        return {
            'outcome': outcome,
            'exit_price': exit_price,
            'exit_time': exit_time,
            'exit_time_formatted': exit_time.strftime('%d-%b %H:%M') if hasattr(exit_time, 'strftime') else str(exit_time),
            'target_price': target_price,
            'stop_loss_price': stop_loss_price,
            'exit_reason': reason,
            'minutes_held': minutes_held,
            'candles_held': candles_held
        }

# Legacy class name for backward compatibility
BacktestEngine = RealDataBacktestEngine
