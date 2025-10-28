import pandas as pd
import logging
from typing import List, Dict, Tuple
from backend.config import Config


logger = logging.getLogger(__name__)

class PatternDetector:
    """Detects candlestick patterns in OHLC data"""
    
    @staticmethod
    def detect_hammer(df: pd.DataFrame) -> List[Dict]:
        """
        Detect Hammer pattern:
        - Long lower shadow (at least 2x body)
        - Small or no upper shadow (max 0.5x body)
        - Small body in upper part of range
        - Body size should be reasonable (not too small)
        - Entry on NEXT candle's open
        """
        patterns = []
        
        # Need at least 2 candles (current + next for entry)
        for i in range(len(df) - 1):  # -1 to ensure we have a next candle
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
                
                # Skip doji or very small candles
                if total_range == 0 or total_range < 0.001:
                    continue
                
                # Body must be at least 10% of total range (not a doji)
                if body / total_range < 0.1:
                    continue
                
                lower_shadow = min(open_price, close_price) - low_price
                upper_shadow = high_price - max(open_price, close_price)
                
                # Skip if body is too small (< 0.5 points for most stocks)
                if body < 0.5:
                    continue
                
                # Hammer criteria - STRICT
                # Lower shadow must be significantly longer than body
                lower_shadow_ratio = lower_shadow / body if body > 0 else 0
                upper_shadow_ratio = upper_shadow / body if body > 0 else 0
                body_ratio = body / total_range
                
                # Check if it's a valid hammer:
                # 1. Lower shadow >= 2x body (main criterion)
                # 2. Upper shadow <= 0.5x body (small or no upper wick)
                # 3. Body is in upper part (at least 10% of range)
                # 4. Lower shadow > upper shadow (dominant lower wick)
                # 5. Lower shadow is significant (> 2 points for most stocks)
                is_hammer = (
                    lower_shadow_ratio >= Config.HAMMER_MIN_LOWER_SHADOW_RATIO and
                    upper_shadow_ratio <= Config.HAMMER_MAX_UPPER_SHADOW_RATIO and
                    body_ratio >= Config.HAMMER_MIN_BODY_RATIO and
                    lower_shadow > upper_shadow and  # Lower shadow dominant
                    lower_shadow >= 2.0  # Absolute minimum lower shadow length
                )
                
                if is_hammer:
                    # Get NEXT candle for entry
                    next_candle = df.iloc[i + 1]
                    next_timestamp = df.index[i + 1]
                    entry_price = float(next_candle['open'])
                    
                    # Additional validation: Entry should be reasonable
                    # Entry shouldn't be too far from hammer's close
                    price_gap = abs(entry_price - close_price) / close_price
                    if price_gap > 0.05:  # Skip if gap > 5%
                        continue
                    
                    patterns.append({
                        'timestamp': next_timestamp,  # Entry timestamp (next candle)
                        'pattern_timestamp': timestamp,  # When hammer formed
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'entry_price': entry_price,  # NEXT candle's open
                        'pattern_type': 'hammer',
                        'lower_shadow': round(lower_shadow, 2),
                        'upper_shadow': round(upper_shadow, 2),
                        'body_size': round(body, 2),
                        'lower_shadow_ratio': round(lower_shadow_ratio, 2),
                        'confidence': PatternDetector._calculate_confidence(
                            lower_shadow_ratio, upper_shadow_ratio, body_ratio, 'hammer'
                        )
                    })
                    
            except Exception as e:
                logger.debug(f"Error detecting pattern at index {i}: {e}")
                continue
        
        logger.info(f"Detected {len(patterns)} hammer patterns")
        return patterns
    
    @staticmethod
    def detect_inverted_hammer(df: pd.DataFrame) -> List[Dict]:
        """
        Detect Inverted Hammer pattern:
        - Long upper shadow (at least 2x body)
        - Small or no lower shadow (max 0.5x body)
        - Small body in lower part of range
        - Entry on NEXT candle's open
        """
        patterns = []
        
        for i in range(len(df) - 1):  # -1 to ensure we have a next candle
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
                
                # Skip doji or very small candles
                if total_range == 0 or total_range < 0.001:
                    continue
                
                # Body must be at least 10% of total range
                if body / total_range < 0.1:
                    continue
                
                lower_shadow = min(open_price, close_price) - low_price
                upper_shadow = high_price - max(open_price, close_price)
                
                # Skip if body is too small
                if body < 0.5:
                    continue
                
                # Inverted Hammer criteria - STRICT
                upper_shadow_ratio = upper_shadow / body if body > 0 else 0
                lower_shadow_ratio = lower_shadow / body if body > 0 else 0
                body_ratio = body / total_range
                
                is_inverted_hammer = (
                    upper_shadow_ratio >= Config.INV_HAMMER_MIN_UPPER_SHADOW_RATIO and
                    lower_shadow_ratio <= Config.INV_HAMMER_MAX_LOWER_SHADOW_RATIO and
                    body_ratio >= Config.INV_HAMMER_MIN_BODY_RATIO and
                    upper_shadow > lower_shadow and  # Upper shadow dominant
                    upper_shadow >= 2.0  # Absolute minimum upper shadow length
                )
                
                if is_inverted_hammer:
                    # Get NEXT candle for entry
                    next_candle = df.iloc[i + 1]
                    next_timestamp = df.index[i + 1]
                    entry_price = float(next_candle['open'])
                    
                    # Additional validation
                    price_gap = abs(entry_price - close_price) / close_price
                    if price_gap > 0.05:  # Skip if gap > 5%
                        continue
                    
                    patterns.append({
                        'timestamp': next_timestamp,  # Entry timestamp
                        'pattern_timestamp': timestamp,  # When pattern formed
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'entry_price': entry_price,  # NEXT candle's open
                        'pattern_type': 'inverted_hammer',
                        'upper_shadow': round(upper_shadow, 2),
                        'lower_shadow': round(lower_shadow, 2),
                        'body_size': round(body, 2),
                        'upper_shadow_ratio': round(upper_shadow_ratio, 2),
                        'confidence': PatternDetector._calculate_confidence(
                            upper_shadow_ratio, lower_shadow_ratio, body_ratio, 'inverted_hammer'
                        )
                    })
                    
            except Exception as e:
                logger.debug(f"Error detecting pattern at index {i}: {e}")
                continue
        
        logger.info(f"Detected {len(patterns)} inverted hammer patterns")
        return patterns
    
    @staticmethod
    def _calculate_confidence(shadow_ratio: float, opposite_shadow: float, 
                            body_ratio: float, pattern_type: str) -> float:
        """Calculate pattern confidence score (0-100)"""
        confidence = 50.0
        
        # Main shadow dominance
        if shadow_ratio >= 3.0:
            confidence += 30
        elif shadow_ratio >= 2.5:
            confidence += 20
        else:
            confidence += 10
        
        # Opposite shadow minimality
        if opposite_shadow <= 0.3:
            confidence += 15
        elif opposite_shadow <= 0.5:
            confidence += 10
        else:
            confidence += 5
        
        # Body significance
        if body_ratio >= 0.15:
            confidence += 5
        
        return min(confidence, 100.0)
    
    @staticmethod
    def is_downtrend(df: pd.DataFrame, index: int, lookback: int = 5) -> bool:
        """
        Check if stock is in downtrend (for hammer context validation)
        Optional: Use this for additional filtering
        """
        if index < lookback:
            return True  # Not enough data, allow pattern
        
        try:
            recent_closes = [float(df.iloc[i]['close']) for i in range(index - lookback, index)]
            # Simple check: if more lower closes than higher
            declines = sum(1 for i in range(1, len(recent_closes)) 
                          if recent_closes[i] < recent_closes[i-1])
            return declines > lookback / 2
        except:
            return True  # Default to allowing pattern
    
    @staticmethod
    def is_uptrend(df: pd.DataFrame, index: int, lookback: int = 5) -> bool:
        """
        Check if stock is in uptrend (for inverted hammer context validation)
        Optional: Use this for additional filtering
        """
        if index < lookback:
            return True
        
        try:
            recent_closes = [float(df.iloc[i]['close']) for i in range(index - lookback, index)]
            advances = sum(1 for i in range(1, len(recent_closes)) 
                          if recent_closes[i] > recent_closes[i-1])
            return advances > lookback / 2
        except:
            return True
