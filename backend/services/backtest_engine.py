# SageForge Hammer Pattern Detection & Backtesting Engine

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import logging
from datetime import datetime, timedelta, time
import asyncio

logger = logging.getLogger(__name__)

class BacktestEngine:
    def __init__(self):
        # FIXED: Much more realistic pattern detection parameters
        self.min_lower_wick_ratio = 1.5  # Lower wick must be at least 1.5x body (was 2.5x - too strict!)
        self.max_upper_wick_ratio = 2.0  # Upper wick can be up to 2x body (was 1x - too strict!)
        
        # ADDED: Trading session times (IST)
        self.market_open = time(9, 15)   # 9:15 AM
        self.market_close = time(15, 30)  # 3:30 PM

    async def run_hammer_analysis(self, stocks: List[str], strategy: str,
                                 target_percent: float, stop_loss_percent: float,
                                 start_date: str, end_date: str) -> Dict:
        logger.info(f"🚀 Starting {strategy} analysis for {len(stocks)} stocks")
        
        # FIXED: Initialize ALL variables at the start (before any try blocks)
        detailed_trades = []
        stock_results = []
        total_profit = 0
        total_safe = 0
        total_stop_loss = 0
        total_no_returns = 0
        
        # Import Angel One service
        from .angel_one_service import angel_one_service
        
        for i, stock in enumerate(stocks):
            try:
                logger.info(f"📊 Processing {stock} ({i+1}/{len(stocks)})")
                
                # Get historical data
                historical_data = await angel_one_service.get_historical_data(
                    stock, start_date, end_date
                )
                
                if historical_data.empty:
                    logger.warning(f"⚠️ No data for {stock}")
                    continue
                    
                logger.info(f"✅ Got {len(historical_data)} candles for {stock}")
                
                # Detect hammer patterns
                patterns = self.detect_hammer_patterns(historical_data, strategy)
                logger.info(f"🔨 Found {len(patterns)} {strategy} patterns for {stock}")
                
                if not patterns:
                    continue
                
                # Initialize per-stock counters
                profit_count = 0
                safe_count = 0
                stop_loss_count = 0
                no_returns_count = 0
                
                for pattern in patterns:
                    outcome = self.test_pattern_outcome(
                        pattern, historical_data, target_percent, stop_loss_percent
                    )
                    
                    # FIXED: Create detailed trade record with new timestamp fields
                    trade_detail = {
                        'stock': str(stock),
                        'timestamp': str(pattern['timestamp']),
                        'pattern_time': pattern['timestamp'].strftime('%d-%b %H:%M') if hasattr(pattern['timestamp'], 'strftime') else str(pattern['timestamp']),
                        'exit_time_formatted': outcome.get('exit_time_formatted', 'N/A'),
                        'pattern_type': str(pattern['pattern_type']).replace('_', ' ').title(),
                        'entry_price': float(pattern['entry_price']),
                        'exit_price': float(outcome.get('exit_price', pattern['entry_price'])),
                        'target_price': float(outcome.get('target_price', 0)),
                        'stop_loss_price': float(outcome.get('stop_loss_price', 0)),
                        'outcome': str(outcome['outcome']),
                        'points_gained': float(outcome.get('exit_price', pattern['entry_price'])) - float(pattern['entry_price']),
                        'percentage_gain': ((float(outcome.get('exit_price', pattern['entry_price'])) - float(pattern['entry_price'])) / float(pattern['entry_price'])) * 100,
                        'minutes_held': min(int(outcome.get('minutes_held', 0)), 45),  # FIXED: Cap at 45 minutes
                        'candles_held': min(int(outcome.get('candles_held', 1)), 3),  # FIXED: Cap at 3 candles
                        'confidence': float(pattern.get('confidence', 50)),
                        'exit_reason': str(outcome.get('exit_reason', 'Unknown'))
                    }
                    
                    # Round values
                    trade_detail['entry_price'] = round(trade_detail['entry_price'], 2)
                    trade_detail['exit_price'] = round(trade_detail['exit_price'], 2)
                    trade_detail['target_price'] = round(trade_detail['target_price'], 2)
                    trade_detail['stop_loss_price'] = round(trade_detail['stop_loss_price'], 2)
                    trade_detail['points_gained'] = round(trade_detail['points_gained'], 2)
                    trade_detail['percentage_gain'] = round(trade_detail['percentage_gain'], 2)
                    trade_detail['confidence'] = round(trade_detail['confidence'], 1)
                    
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
                    'profit_rate': round(float(profit_rate), 2)
                })
                
                # FIXED: Update totals (variables now exist)
                total_profit += profit_count
                total_safe += safe_count
                total_stop_loss += stop_loss_count
                total_no_returns += no_returns_count
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error processing {stock}: {str(e)}")
                # FIXED: Variables are now defined, so this won't crash
                continue
        
        # Calculate overall results (variables are now guaranteed to exist)
        total_patterns = total_profit + total_safe + total_stop_loss + total_no_returns
        
        if total_patterns == 0:
            logger.warning(f"⚠️ No patterns found across all {len(stocks)} stocks!")
            return {
                'profit_rate': 0.0,
                'safe_rate': 0.0,
                'stop_loss_rate': 0.0,
                'no_returns_rate': 0.0,
                'total_patterns': 0,
                'strategy': str(strategy).replace('_', ' ').title(),
                'period': f"{start_date} to {end_date}",
                'stocks_analyzed': 0,
                'target_percent': float(target_percent),
                'stop_loss_percent': float(stop_loss_percent),
                'stock_results': [],
                'detailed_trades': [],
                'message': f'No {str(strategy).replace("_", " ")} patterns detected',
                'timeframe': 'Intraday 15-minute'
            }
        
        # Calculate rates
        profit_rate = round((total_profit / total_patterns) * 100, 2)
        safe_rate = round((total_safe / total_patterns) * 100, 2)
        stop_loss_rate = round((total_stop_loss / total_patterns) * 100, 2)
        no_returns_rate = round((total_no_returns / total_patterns) * 100, 2)
        
        # Sort detailed trades by timestamp (most recent first)
        detailed_trades.sort(key=lambda x: x['timestamp'], reverse=True)
        
        logger.info(f"✅ Analysis complete: {total_patterns} patterns, {len(detailed_trades)} detailed trades")
        
        return {
            'profit_rate': float(profit_rate),
            'safe_rate': float(safe_rate),
            'stop_loss_rate': float(stop_loss_rate),
            'no_returns_rate': float(no_returns_rate),
            'total_patterns': int(total_patterns),
            'strategy': str(strategy).replace('_', ' ').title(),
            'period': f"{start_date} to {end_date}",
            'stocks_analyzed': int(len([s for s in stock_results if s['patterns_found'] > 0])),
            'target_percent': float(target_percent),
            'stop_loss_percent': float(stop_loss_percent),
            'stock_results': sorted(stock_results, key=lambda x: x['profit_rate'], reverse=True)[:20],
            'detailed_trades': detailed_trades,
            'timeframe': 'Intraday 15-minute'
        }

    def detect_hammer_patterns(self, df: pd.DataFrame, pattern_type: str) -> List[Dict]:
        """Simple and effective hammer pattern detection"""
        if df.empty:
            logger.warning("❌ DataFrame is empty")
            return []
            
        logger.info(f"🔍 PATTERN DETECTION:")
        logger.info(f"   Total candles: {len(df)}")
        logger.info(f"   Date range: {df.index.min()} to {df.index.max()}")
        
        patterns = []
        
        # Simple pattern detection - check each candle
        for i in range(len(df)):
            try:
                row = df.iloc[i]
                timestamp = df.index[i]
                
                open_val = float(row['open'])
                high_val = float(row['high'])
                low_val = float(row['low'])
                close_val = float(row['close'])
                
                # Check for patterns
                is_pattern = False
                if pattern_type == "hammer":
                    is_pattern = self._is_simple_hammer(open_val, high_val, low_val, close_val)
                elif pattern_type == "inverted_hammer":
                    is_pattern = self._is_simple_inverted_hammer(open_val, high_val, low_val, close_val)
                
                if is_pattern:
                    pattern = {
                        'timestamp': timestamp,
                        'open': open_val,
                        'high': high_val,
                        'low': low_val,
                        'close': close_val,
                        'pattern_type': pattern_type,
                        'entry_price': close_val,  # Entry at close of hammer candle
                        'confidence': 75.0
                    }
                    patterns.append(pattern)
                    
            except Exception as e:
                if i < 3:  # Only log first few errors
                    logger.error(f"❌ Error processing candle {i}: {e}")
        
        logger.info(f"✅ Found {len(patterns)} {pattern_type} patterns")
        return patterns

    def _is_simple_hammer(self, open_price: float, high_price: float, low_price: float, close_price: float) -> bool:
        """Simple hammer detection"""
        try:
            if high_price <= low_price:
                return False
                
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range <= 0:
                return False
            
            # Lenient hammer conditions
            lower_dominance = lower_shadow / total_range
            upper_ratio = upper_shadow / total_range
            
            conditions = [
                lower_dominance >= 0.4,  # Lower shadow at least 40% of range
                upper_ratio <= 0.3,      # Upper shadow at most 30% of range
                lower_shadow > upper_shadow,  # Lower shadow longer
                total_range > 0.01       # Meaningful range
            ]
            
            return all(conditions)
        except Exception:
            return False

    def _is_simple_inverted_hammer(self, open_price: float, high_price: float, low_price: float, close_price: float) -> bool:
        """Simple inverted hammer detection"""
        try:
            if high_price <= low_price:
                return False
                
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range <= 0:
                return False
            
            # Lenient inverted hammer conditions
            upper_dominance = upper_shadow / total_range
            lower_ratio = lower_shadow / total_range
            
            conditions = [
                upper_dominance >= 0.4,  # Upper shadow at least 40% of range
                lower_ratio <= 0.3,      # Lower shadow at most 30% of range
                upper_shadow > lower_shadow,  # Upper shadow longer
                total_range > 0.01       # Meaningful range
            ]
            
            return all(conditions)
        except Exception:
            return False

    def test_pattern_outcome(self, pattern: Dict, df: pd.DataFrame,
                           target_percent: float, stop_loss_percent: float) -> Dict:
        """
        FIXED: Realistic intraday constraints for Indian market (375 min total)
        Exit within 2-3 candles maximum (30-45 minutes for 15-min candles)
        """
        entry_price = pattern['entry_price']
        entry_time = pattern['timestamp']
        
        # Calculate target and stop-loss levels
        target_price = entry_price * (1 + target_percent / 100)
        stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
        
        try:
            # Get future data after pattern entry
            future_data = df[df.index > entry_time].copy()
            
            if future_data.empty:
                return {
                    'outcome': 'no_returns',
                    'exit_price': entry_price,
                    'exit_time': entry_time,
                    'minutes_held': 0,
                    'candles_held': 0,
                    'pattern_time': entry_time.strftime('%d-%b %H:%M') if hasattr(entry_time, 'strftime') else str(entry_time),
                    'exit_time_formatted': 'N/A',
                    'exit_reason': 'No future data'
                }

            # FIXED: Limit to same trading day and maximum 3 candles
            same_day_candles = []
            entry_date = entry_time.date() if hasattr(entry_time, 'date') else str(entry_time)[:10]
            
            for timestamp, row in future_data.iterrows():
                # Stop if different trading day
                candle_date = timestamp.date() if hasattr(timestamp, 'date') else str(timestamp)[:10]
                if str(candle_date) != str(entry_date):
                    break
                    
                # FIXED: Maximum 3 candles (45 minutes for 15-min timeframe)
                if len(same_day_candles) >= 3:
                    break
                    
                same_day_candles.append((timestamp, row))

            if not same_day_candles:
                return {
                    'outcome': 'no_returns',
                    'exit_price': entry_price,
                    'exit_time': entry_time,
                    'minutes_held': 0,
                    'candles_held': 0,
                    'pattern_time': entry_time.strftime('%d-%b %H:%M') if hasattr(entry_time, 'strftime') else str(entry_time),
                    'exit_time_formatted': 'N/A',
                    'exit_reason': 'No same-day data'
                }

            # Test each candle (maximum 3 candles = 45 minutes)
            for candle_num, (timestamp, row) in enumerate(same_day_candles, 1):
                try:
                    # FIXED: Calculate realistic minutes (15-min intervals)
                    minutes_held = candle_num * 15  # 15, 30, or 45 minutes max
                    
                    high_price = float(row['high'])
                    low_price = float(row['low'])
                    close_price = float(row['close'])

                    # Check TARGET hit (profit)
                    if high_price >= target_price:
                        return {
                            'outcome': 'profit',
                            'exit_price': target_price,
                            'exit_time': timestamp,
                            'minutes_held': minutes_held,
                            'candles_held': candle_num,
                            'pattern_time': entry_time.strftime('%d-%b %H:%M') if hasattr(entry_time, 'strftime') else str(entry_time),
                            'exit_time_formatted': timestamp.strftime('%d-%b %H:%M') if hasattr(timestamp, 'strftime') else str(timestamp),
                            'exit_reason': f'Target hit in candle {candle_num}'
                        }

                    # Check STOP LOSS hit
                    if low_price <= stop_loss_price:
                        return {
                            'outcome': 'stop_loss',
                            'exit_price': stop_loss_price,
                            'exit_time': timestamp,
                            'minutes_held': minutes_held,
                            'candles_held': candle_num,
                            'pattern_time': entry_time.strftime('%d-%b %H:%M') if hasattr(entry_time, 'strftime') else str(entry_time),
                            'exit_time_formatted': timestamp.strftime('%d-%b %H:%M') if hasattr(timestamp, 'strftime') else str(timestamp),
                            'exit_reason': f'Stop loss hit in candle {candle_num}'
                        }

                except Exception as e:
                    continue

            # Final outcome after 3 candles (forced exit)
            if same_day_candles:
                final_timestamp, final_row = same_day_candles[-1]
                final_price = float(final_row['close'])
                final_minutes = len(same_day_candles) * 15  # 15, 30, or 45 minutes
                
                outcome = 'safe' if final_price > entry_price else 'no_returns'
                
                return {
                    'outcome': outcome,
                    'exit_price': final_price,
                    'exit_time': final_timestamp,
                    'minutes_held': final_minutes,
                    'candles_held': len(same_day_candles),
                    'pattern_time': entry_time.strftime('%d-%b %H:%M') if hasattr(entry_time, 'strftime') else str(entry_time),
                    'exit_time_formatted': final_timestamp.strftime('%d-%b %H:%M') if hasattr(final_timestamp, 'strftime') else str(final_timestamp),
                    'exit_reason': f'Forced exit after {len(same_day_candles)} candles'
                }

        except Exception as e:
            logger.error(f"Error in outcome testing: {e}")
            return {
                'outcome': 'no_returns',
                'exit_price': entry_price,
                'exit_time': entry_time,
                'minutes_held': 0,
                'candles_held': 0,
                'pattern_time': entry_time.strftime('%d-%b %H:%M') if hasattr(entry_time, 'strftime') else str(entry_time),
                'exit_time_formatted': 'N/A',
                'exit_reason': 'Calculation error'
            }

    # Keep your existing methods for compatibility
    def _detect_simple_hammer(self, open_price, high_price, low_price, close_price) -> bool:
        """ULTRA-SIMPLE hammer detection - very lenient for testing"""
        try:
            if high_price <= low_price:
                return False
            
            body = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range <= 0:
                return False
            
            # VERY LENIENT CONDITIONS (for testing)
            lower_dominance = lower_shadow / total_range
            upper_ratio = upper_shadow / total_range
            
            conditions = [
                lower_dominance >= 0.25,  # Lower shadow at least 25% of range
                upper_ratio <= 0.5,       # Upper shadow at most 50% of range
                lower_shadow >= upper_shadow * 0.5,  # Lower shadow somewhat longer
                total_range > 0.01
            ]
            
            return all(conditions)
        except Exception:
            return False

    def _detect_simple_inverted_hammer(self, open_price, high_price, low_price, close_price) -> bool:
        """ULTRA-SIMPLE inverted hammer detection"""
        try:
            if high_price <= low_price:
                return False
            
            body = abs(close_price - open_price)
            lower_shadow = min(open_price, close_price) - low_price
            upper_shadow = high_price - max(open_price, close_price)
            total_range = high_price - low_price
            
            if total_range <= 0:
                return False
            
            # VERY LENIENT CONDITIONS
            upper_dominance = upper_shadow / total_range
            lower_ratio = lower_shadow / total_range
            
            conditions = [
                upper_dominance >= 0.25,  # Upper shadow at least 25% of range
                lower_ratio <= 0.5,       # Lower shadow at most 50% of range
                upper_shadow >= lower_shadow * 0.5,  # Upper shadow somewhat longer
                total_range > 0.01
            ]
            
            return all(conditions)
        except Exception:
            return False

    def _is_hammer_realistic(self, candle, column_map) -> bool:
        """FIXED: Much more realistic hammer pattern detection"""
        try:
            open_price = float(candle[column_map['open']])
            high_price = float(candle[column_map['high']])
            low_price = float(candle[column_map['low']])
            close_price = float(candle[column_map['close']])
        except (ValueError, KeyError) as e:
            return False
            
        # Basic validation
        if high_price <= low_price or high_price < max(open_price, close_price) or low_price > min(open_price, close_price):
            return False
            
        # Calculate components
        body = abs(close_price - open_price)
        lower_shadow = min(open_price, close_price) - low_price
        upper_shadow = high_price - max(open_price, close_price)
        total_range = high_price - low_price
        
        # Handle very small bodies
        if body < 0.1:
            body = 0.1
            
        # FIXED: Much more realistic hammer conditions
        lower_wick_ratio = lower_shadow / body
        upper_wick_ratio = upper_shadow / body
        
        # Realistic conditions for hammer
        conditions = [
            lower_wick_ratio >= self.min_lower_wick_ratio,  # Lower wick ≥ 1.5x body (was 2.5x)
            upper_wick_ratio <= self.max_upper_wick_ratio,  # Upper wick ≤ 2x body (was 1x)
            lower_shadow > 0,    # Must have some lower wick
            total_range > 0      # Valid price range
        ]
        
        return all(conditions)

    def _is_inverted_hammer_realistic(self, candle, column_map) -> bool:
        """FIXED: Much more realistic inverted hammer pattern detection"""
        try:
            open_price = float(candle[column_map['open']])
            high_price = float(candle[column_map['high']])
            low_price = float(candle[column_map['low']])
            close_price = float(candle[column_map['close']])
        except (ValueError, KeyError):
            return False
            
        # Basic validation
        if high_price <= low_price or high_price < max(open_price, close_price) or low_price > min(open_price, close_price):
            return False
            
        # Calculate components
        body = abs(close_price - open_price)
        lower_shadow = min(open_price, close_price) - low_price
        upper_shadow = high_price - max(open_price, close_price)
        total_range = high_price - low_price
        
        # Handle very small bodies
        if body < 0.1:
            body = 0.1
            
        # FIXED: Much more realistic inverted hammer conditions
        upper_wick_ratio = upper_shadow / body
        lower_wick_ratio = lower_shadow / body
        
        # Realistic conditions for inverted hammer
        conditions = [
            upper_wick_ratio >= self.min_lower_wick_ratio,  # Upper wick ≥ 1.5x body (was 2.5x)
            lower_wick_ratio <= self.max_upper_wick_ratio,  # Lower wick ≤ 2x body (was 1x)
            upper_shadow > 0,    # Must have some upper wick
            total_range > 0      # Valid price range
        ]
        
        return all(conditions)

    def _calculate_pattern_confidence_realistic(self, candle, column_map, pattern_type: str) -> float:
        """FIXED: More realistic confidence calculation"""
        try:
            open_price = float(candle[column_map['open']])
            high_price = float(candle[column_map['high']])
            low_price = float(candle[column_map['low']])
            close_price = float(candle[column_map['close']])
        except (ValueError, KeyError):
            return 50.0
            
        body = abs(close_price - open_price)
        total_range = high_price - low_price
        
        if total_range == 0:
            return 50.0
            
        if pattern_type == 'hammer':
            lower_shadow = min(open_price, close_price) - low_price
            lower_dominance = (lower_shadow / total_range) * 100
            return max(50, min(100, lower_dominance * 1.2))
        else:  # inverted_hammer
            upper_shadow = high_price - max(open_price, close_price)
            upper_dominance = (upper_shadow / total_range) * 100
            return max(50, min(100, upper_dominance * 1.2))

    # Keep your existing methods for compatibility
    def _is_hammer(self, candle) -> bool:
        """Legacy method - redirects to realistic version"""
        column_map = {'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'}
        return self._is_hammer_realistic(candle, column_map)

    def _is_inverted_hammer(self, candle) -> bool:
        """Legacy method - redirects to realistic version"""
        column_map = {'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'}
        return self._is_inverted_hammer_realistic(candle, column_map)

    def _calculate_pattern_confidence(self, candle, pattern_type: str) -> float:
        """Legacy method - redirects to realistic version"""
        column_map = {'open': 'open', 'high': 'high', 'low': 'low', 'close': 'close'}
        return self._calculate_pattern_confidence_realistic(candle, column_map, pattern_type)