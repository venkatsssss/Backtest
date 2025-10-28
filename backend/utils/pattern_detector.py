import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Tuple
from backend.config import Config


logger = logging.getLogger(__name__)

class PatternDetector:
    """Detects candlestick patterns in OHLC data"""
    
    @staticmethod
    def detect_hammer(df: pd.DataFrame) -> List[Dict]:
        """
        Detect Hammer pattern with SIZE validation:
        - Lower shadow significantly longer than upper shadow
        - Lower shadow at least 1.5x body size
        - Candle must be significant size (not tiny)
        - Filters based on average candle size
        """
        patterns = []
        
        # Calculate average candle metrics for filtering
        df_copy = df.copy()
        df_copy['range'] = df_copy['high'] - df_copy['low']
        df_copy['body'] = abs(df_copy['close'] - df_copy['open'])
        
        # Get average range and body over lookback period
        avg_range = df_copy['range'].rolling(window=20, min_periods=5).mean()
        avg_body = df_copy['body'].rolling(window=20, min_periods=5).mean()
        
        # Need at least 1 candle after for entry price
        for i in range(len(df) - 1):
            try:
                candle = df.iloc[i]
                timestamp = df.index[i]
                
                open_price = float(candle['open'])
                high_price = float(candle['high'])
                low_price = float(candle['low'])
                close_price = float(candle['close'])
                
                # Calculate body and shadows
                body = abs(close_price - open_price)
                total_range = high_price - low_price
                
                # Skip if no range
                if total_range == 0 or total_range < 0.01:
                    continue
                
                lower_shadow = min(open_price, close_price) - low_price
                upper_shadow = high_price - max(open_price, close_price)
                
                # Doji check - skip
                if body == 0:
                    continue
                
                # SIZE VALIDATION - Critical for filtering small candles
                # 1. Minimum absolute size requirements
                if total_range < 2.0:  # Candle range must be at least 2 rupees
                    continue
                
                if lower_shadow < 1.0:  # Lower shadow must be at least 1 rupee
                    continue
                
                if body < 0.3:  # Body must be at least 0.3 rupees
                    continue
                
                # 2. Relative size validation (compared to recent average)
                if i >= 5:  # Need some history
                    current_avg_range = avg_range.iloc[i]
                    current_avg_body = avg_body.iloc[i]
                    
                    if pd.notna(current_avg_range) and current_avg_range > 0:
                        # Range should be at least 50% of average range
                        if total_range < (current_avg_range * 0.5):
                            continue
                    
                    if pd.notna(current_avg_body) and current_avg_body > 0:
                        # Body should be at least 30% of average body
                        if body < (current_avg_body * 0.3):
                            continue
                
                # Calculate ratios
                lower_shadow_ratio = lower_shadow / body
                upper_shadow_ratio = upper_shadow / body
                body_ratio = body / total_range
                
                # Hammer criteria (same as before)
                is_hammer = (
                    lower_shadow > upper_shadow and  # Lower shadow dominant
                    lower_shadow_ratio >= 1.5 and     # Lower shadow >= 1.5x body
                    upper_shadow_ratio <= 1.0 and     # Upper shadow <= body
                    body_ratio >= 0.05 and            # Body >= 5% of range
                    lower_shadow >= 1.5               # Absolute minimum shadow (1.5 points)
                )
                
                if is_hammer:
                    # Get NEXT candle for entry price
                    next_candle = df.iloc[i + 1]
                    entry_price = float(next_candle['open'])
                    
                    # Additional: Skip if next candle gaps too much
                    price_gap = abs(entry_price - close_price) / close_price
                    if price_gap > 0.03:  # Skip if gap > 3%
                        continue
                    
                    patterns.append({
                        'timestamp': timestamp,
                        'entry_timestamp': df.index[i + 1],
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'entry_price': entry_price,
                        'pattern_type': 'hammer',
                        'lower_shadow': round(lower_shadow, 2),
                        'upper_shadow': round(upper_shadow, 2),
                        'body_size': round(body, 2),
                        'total_range': round(total_range, 2),
                        'lower_shadow_ratio': round(lower_shadow_ratio, 2),
                        'upper_shadow_ratio': round(upper_shadow_ratio, 2),
                        'avg_range': round(avg_range.iloc[i], 2) if i >= 5 and pd.notna(avg_range.iloc[i]) else 0,
                        'confidence': PatternDetector._calculate_confidence(
                            lower_shadow_ratio, upper_shadow_ratio, body_ratio, total_range
                        )
                    })
                    
            except Exception as e:
                logger.debug(f"Error detecting pattern at index {i}: {e}")
                continue
        
        logger.info(f"Detected {len(patterns)} hammer patterns (after size filtering)")
        return patterns
    
    @staticmethod
    def detect_inverted_hammer(df: pd.DataFrame) -> List[Dict]:
        """
        Detect Inverted Hammer pattern with SIZE validation
        """
        patterns = []
        
        # Calculate average metrics
        df_copy = df.copy()
        df_copy['range'] = df_copy['high'] - df_copy['low']
        df_copy['body'] = abs(df_copy['close'] - df_copy['open'])
        
        avg_range = df_copy['range'].rolling(window=20, min_periods=5).mean()
        avg_body = df_copy['body'].rolling(window=20, min_periods=5).mean()
        
        for i in range(len(df) - 1):
            try:
                candle = df.iloc[i]
                timestamp = df.index[i]
                
                open_price = float(candle['open'])
                high_price = float(candle['high'])
                low_price = float(candle['low'])
                close_price = float(candle['close'])
                
                body = abs(close_price - open_price)
                total_range = high_price - low_price
                
                if total_range == 0 or total_range < 0.01:
                    continue
                
                lower_shadow = min(open_price, close_price) - low_price
                upper_shadow = high_price - max(open_price, close_price)
                
                if body == 0:
                    continue
                
                # SIZE VALIDATION (same as hammer)
                if total_range < 2.0:
                    continue
                
                if upper_shadow < 1.0:  # Upper shadow minimum
                    continue
                
                if body < 0.3:
                    continue
                
                # Relative size validation
                if i >= 5:
                    current_avg_range = avg_range.iloc[i]
                    current_avg_body = avg_body.iloc[i]
                    
                    if pd.notna(current_avg_range) and current_avg_range > 0:
                        if total_range < (current_avg_range * 0.5):
                            continue
                    
                    if pd.notna(current_avg_body) and current_avg_body > 0:
                        if body < (current_avg_body * 0.3):
                            continue
                
                upper_shadow_ratio = upper_shadow / body
                lower_shadow_ratio = lower_shadow / body
                body_ratio = body / total_range
                
                # Inverted hammer criteria
                is_inverted_hammer = (
                    upper_shadow > lower_shadow and
                    upper_shadow_ratio >= 1.5 and
                    lower_shadow_ratio <= 1.0 and
                    body_ratio >= 0.05 and
                    upper_shadow >= 1.5
                )
                
                if is_inverted_hammer:
                    next_candle = df.iloc[i + 1]
                    entry_price = float(next_candle['open'])
                    
                    price_gap = abs(entry_price - close_price) / close_price
                    if price_gap > 0.03:
                        continue
                    
                    patterns.append({
                        'timestamp': timestamp,
                        'entry_timestamp': df.index[i + 1],
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'entry_price': entry_price,
                        'pattern_type': 'inverted_hammer',
                        'upper_shadow': round(upper_shadow, 2),
                        'lower_shadow': round(lower_shadow, 2),
                        'body_size': round(body, 2),
                        'total_range': round(total_range, 2),
                        'upper_shadow_ratio': round(upper_shadow_ratio, 2),
                        'lower_shadow_ratio': round(lower_shadow_ratio, 2),
                        'avg_range': round(avg_range.iloc[i], 2) if i >= 5 and pd.notna(avg_range.iloc[i]) else 0,
                        'confidence': PatternDetector._calculate_confidence(
                            upper_shadow_ratio, lower_shadow_ratio, body_ratio, total_range
                        )
                    })
                    
            except Exception as e:
                logger.debug(f"Error detecting pattern at index {i}: {e}")
                continue
        
        logger.info(f"Detected {len(patterns)} inverted hammer patterns (after size filtering)")
        return patterns
    
    @staticmethod
    def _calculate_confidence(shadow_ratio: float, opposite_shadow: float, 
                            body_ratio: float, total_range: float) -> float:
        """
        Calculate pattern confidence score (0-100)
        Now includes size factor
        """
        confidence = 40.0
        
        # Main shadow dominance
        if shadow_ratio >= 3.0:
            confidence += 30
        elif shadow_ratio >= 2.5:
            confidence += 25
        elif shadow_ratio >= 2.0:
            confidence += 20
        elif shadow_ratio >= 1.5:
            confidence += 15
        
        # Opposite shadow minimality
        if opposite_shadow <= 0.3:
            confidence += 15
        elif opposite_shadow <= 0.5:
            confidence += 12
        elif opposite_shadow <= 0.7:
            confidence += 8
        elif opposite_shadow <= 1.0:
            confidence += 5
        
        # Body significance
        if body_ratio >= 0.15:
            confidence += 10
        elif body_ratio >= 0.10:
            confidence += 7
        elif body_ratio >= 0.05:
            confidence += 3
        
        # Size bonus - larger candles get higher confidence
        if total_range >= 5.0:
            confidence += 5
        elif total_range >= 3.0:
            confidence += 3
        
        return min(confidence, 100.0)