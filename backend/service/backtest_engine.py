import pandas as pd
import logging
from datetime import datetime, time
from typing import List, Dict
from backend.utils.pattern_detector import PatternDetector
from backend.config import Config

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Backtesting engine for candlestick patterns"""
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.market_open = time(9, 15)
        self.market_close = time(15, 30)
    
    async def run_backtest(
        self,
        historical_data: Dict[str, pd.DataFrame],
        strategy: str,
        target_percent: float,
        stop_loss_percent: float
    ) -> Dict:
        """
        Run backtest on historical data
        
        Args:
            historical_data: Dict of {symbol: DataFrame}
            strategy: 'hammer' or 'inverted_hammer'
            target_percent: Target profit percentage
            stop_loss_percent: Stop loss percentage
        
        Returns:
            Dict with backtest results
        """
        logger.info(f"Starting {strategy} backtest for {len(historical_data)} stocks")
        
        all_trades = []
        total_target_hits = 0
        total_stop_losses = 0
        total_eod_exits = 0
        total_points = 0.0
        
        for symbol, df in historical_data.items():
            try:
                logger.info(f"Analyzing {symbol}...")
                
                # Detect patterns
                if strategy == 'hammer':
                    patterns = self.pattern_detector.detect_hammer(df)
                elif strategy == 'inverted_hammer':
                    patterns = self.pattern_detector.detect_inverted_hammer(df)
                else:
                    logger.error(f"Unknown strategy: {strategy}")
                    continue
                
                if not patterns:
                    logger.info(f"No {strategy} patterns found for {symbol}")
                    continue
                
                logger.info(f"Found {len(patterns)} {strategy} patterns in {symbol}")
                
                # Test each pattern
                for pattern in patterns:
                    trade_result = self._simulate_trade(
                        symbol=symbol,
                        pattern=pattern,
                        df=df,
                        target_percent=target_percent,
                        stop_loss_percent=stop_loss_percent
                    )
                    
                    if trade_result:
                        all_trades.append(trade_result)
                        
                        # Update counters
                        if trade_result['outcome'] == 'target_hit':
                            total_target_hits += 1
                        elif trade_result['outcome'] == 'stop_loss':
                            total_stop_losses += 1
                        else:
                            total_eod_exits += 1
                        
                        total_points += trade_result['points_gained']
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        # Calculate summary statistics
        total_patterns = len(all_trades)
        
        if total_patterns == 0:
            return self._empty_result(strategy)
        
        target_hit_rate = (total_target_hits / total_patterns) * 100
        stop_loss_rate = (total_stop_losses / total_patterns) * 100
        avg_return = sum(t['percentage_return'] for t in all_trades) / total_patterns
        
        logger.info(f"✅ Backtest completed: {total_patterns} trades analyzed")
        
        return {
            'total_patterns': total_patterns,
            'target_hit_count': total_target_hits,
            'stop_loss_count': total_stop_losses,
            'eod_exit_count': total_eod_exits,
            'target_hit_rate': round(target_hit_rate, 2),
            'stop_loss_rate': round(stop_loss_rate, 2),
            'avg_return': round(avg_return, 2),
            'total_points_gained': round(total_points, 2),
            'trades': all_trades
        }
    
    def _simulate_trade(
        self,
        symbol: str,
        pattern: Dict,
        df: pd.DataFrame,
        target_percent: float,
        stop_loss_percent: float
    ) -> Dict:
        """
        Simulate a single trade based on pattern
        NOW TRACKS: Maximum profit reached during trade
        
        Returns:
            Dict with trade details including max_profit_reached
        """
        try:
            # Pattern formed at this time
            pattern_time = pattern['timestamp']
            
            # Entry at next candle (already in pattern dict)
            entry_time = pattern['entry_timestamp']
            entry_price = pattern['entry_price']
            
            # Calculate target and stop loss prices
            target_price = entry_price * (1 + target_percent / 100)
            stop_loss_price = entry_price * (1 - stop_loss_percent / 100)
            
            # Get future candles AFTER entry (same day only)
            future_candles = df[df.index > entry_time].copy()
            
            if future_candles.empty:
                return None
            
            # Filter same day candles only (intraday)
            entry_date = entry_time.date()
            same_day_candles = future_candles[
                future_candles.index.date == entry_date
            ]
            
            if same_day_candles.empty:
                return None
            
            # Initialize tracking variables
            exit_price = entry_price
            exit_time = entry_time
            exit_reason = 'eod_exit'
            outcome = 'eod_exit'
            minutes_held = 0
            candles_held = 0
            
            # NEW: Track maximum profit reached
            max_profit_points = 0.0  # Maximum profit in points
            max_profit_percent = 0.0  # Maximum profit in percentage
            max_loss_points = 0.0  # Maximum loss (for additional insight)
            
            for idx, (timestamp, candle) in enumerate(same_day_candles.iterrows(), 1):
                high_price = float(candle['high'])
                low_price = float(candle['low'])
                close_price = float(candle['close'])
                
                # Track maximum profit reached (from HIGH of each candle)
                profit_at_high = high_price - entry_price
                if profit_at_high > max_profit_points:
                    max_profit_points = profit_at_high
                    max_profit_percent = (profit_at_high / entry_price) * 100
                
                # Track maximum loss reached (from LOW of each candle)
                loss_at_low = entry_price - low_price
                if loss_at_low > max_loss_points:
                    max_loss_points = loss_at_low
                
                # Check if target hit (priority)
                if high_price >= target_price:
                    exit_price = target_price
                    exit_time = timestamp
                    exit_reason = 'Target hit'
                    outcome = 'target_hit'
                    minutes_held = (timestamp - entry_time).total_seconds() / 60
                    candles_held = idx
                    # Max profit will be at least the target
                    if max_profit_points < (target_price - entry_price):
                        max_profit_points = target_price - entry_price
                        max_profit_percent = target_percent
                    break
                
                # Check if stop loss hit
                if low_price <= stop_loss_price:
                    exit_price = stop_loss_price
                    exit_time = timestamp
                    exit_reason = 'Stop loss triggered'
                    outcome = 'stop_loss'
                    minutes_held = (timestamp - entry_time).total_seconds() / 60
                    candles_held = idx
                    break
                
                # Check if market close (3:30 PM)
                if timestamp.time() >= self.market_close:
                    exit_price = close_price
                    exit_time = timestamp
                    exit_reason = 'End of day exit'
                    outcome = 'eod_exit'
                    minutes_held = (timestamp - entry_time).total_seconds() / 60
                    candles_held = idx
                    break
            
            # If loop completes without break, use last candle
            if exit_time == entry_time and len(same_day_candles) > 0:
                last_candle = same_day_candles.iloc[-1]
                exit_price = float(last_candle['close'])
                exit_time = same_day_candles.index[-1]
                minutes_held = (exit_time - entry_time).total_seconds() / 60
                candles_held = len(same_day_candles)
            
            # Calculate final returns
            points_gained = exit_price - entry_price
            percentage_return = (points_gained / entry_price) * 100
            
            # If max profit is still 0 (never went into profit), keep it as 0
            if max_profit_points < 0:
                max_profit_points = 0.0
                max_profit_percent = 0.0
            
            return {
                'stock': symbol,
                'pattern_date': pattern_time.strftime('%Y-%m-%d'),
                'pattern_time': pattern_time.strftime('%H:%M'),
                'entry_price': round(entry_price, 2),
                'target_price': round(target_price, 2),
                'stop_loss_price': round(stop_loss_price, 2),
                'exit_price': round(exit_price, 2),
                'exit_time': exit_time.strftime('%Y-%m-%d %H:%M'),
                'exit_reason': exit_reason,
                'points_gained': round(points_gained, 2),
                'percentage_return': round(percentage_return, 2),
                'minutes_held': int(minutes_held),
                'candles_held': candles_held,
                'outcome': outcome,
                
                # NEW FIELDS
                'max_profit_points': round(max_profit_points, 2),
                'max_profit_percent': round(max_profit_percent, 2),
                'max_loss_points': round(max_loss_points, 2),
                
                # Additional pattern info
                'lower_shadow': pattern.get('lower_shadow', 0),
                'upper_shadow': pattern.get('upper_shadow', 0),
                'body_size': pattern.get('body_size', 0),
                'confidence': pattern.get('confidence', 0)
            }
            
        except Exception as e:
            logger.error(f"Error simulating trade: {e}")
            return None
    
    def _empty_result(self, strategy: str) -> Dict:
        """Return empty result structure"""
        return {
            'total_patterns': 0,
            'target_hit_count': 0,
            'stop_loss_count': 0,
            'eod_exit_count': 0,
            'target_hit_rate': 0.0,
            'stop_loss_rate': 0.0,
            'avg_return': 0.0,
            'total_points_gained': 0.0,
            'trades': [],
            'message': f'No {strategy} patterns found in the selected period'
        }