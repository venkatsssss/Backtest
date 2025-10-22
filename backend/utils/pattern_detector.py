import pandas as pd
import logging
from typing import List, Dict, Tuple
from .config import Config


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
        """
        patterns = []
        
        for i in range(len(df)):
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
                
                if total_range == 0 or body == 0:
                    continue
                
                lower_shadow = min(open_price, close_price) - low_price
                upper_shadow = high_price - max(open_price, close_price)
                
                # Hammer criteria
                lower_shadow_ratio = lower_shadow / body if body > 0 else 0
                upper_shadow_ratio = upper_shadow / body if body > 0 else 0
                body_ratio = body / total_range
                
                is_hammer = (
                    lower_shadow_ratio >= Config.HAMMER_MIN_LOWER_SHADOW_RATIO and
                    upper_shadow_ratio <= Config.HAMMER_MAX_UPPER_SHADOW_RATIO and
                    body_ratio >= Config.HAMMER_MIN_BODY_RATIO and
                    lower_shadow > upper_shadow  # Lower shadow dominant
                )
                
                if is_hammer:
                    patterns.append({
                        'timestamp': timestamp,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'entry_price': close_price,
                        'pattern_type': 'hammer',
                        'confidence': PatternDetector._calculate_confidence(
                            lower_shadow_ratio, upper_shadow_ratio, body_ratio, 'hammer'
                        )
                    })
                    
            except Exception as e:
                logger.debug(f"Error detecting pattern at index {i}: {e}")
                continue
        
        return patterns
    
    @staticmethod
    def detect_inverted_hammer(df: pd.DataFrame) -> List[Dict]:
        """
        Detect Inverted Hammer pattern:
        - Long upper shadow (at least 2x body)
        - Small or no lower shadow (max 0.5x body)
        - Small body in lower part of range
        """
        patterns = []
        
        for i in range(len(df)):
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
                
                if total_range == 0 or body == 0:
                    continue
                
                lower_shadow = min(open_price, close_price) - low_price
                upper_shadow = high_price - max(open_price, close_price)
                
                # Inverted Hammer criteria
                upper_shadow_ratio = upper_shadow / body if body > 0 else 0
                lower_shadow_ratio = lower_shadow / body if body > 0 else 0
                body_ratio = body / total_range
                
                is_inverted_hammer = (
                    upper_shadow_ratio >= Config.INV_HAMMER_MIN_UPPER_SHADOW_RATIO and
                    lower_shadow_ratio <= Config.INV_HAMMER_MAX_LOWER_SHADOW_RATIO and
                    body_ratio >= Config.INV_HAMMER_MIN_BODY_RATIO and
                    upper_shadow > lower_shadow  # Upper shadow dominant
                )
                
                if is_inverted_hammer:
                    patterns.append({
                        'timestamp': timestamp,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'entry_price': close_price,
                        'pattern_type': 'inverted_hammer',
                        'confidence': PatternDetector._calculate_confidence(
                            upper_shadow_ratio, lower_shadow_ratio, body_ratio, 'inverted_hammer'
                        )
                    })
                    
            except Exception as e:
                logger.debug(f"Error detecting pattern at index {i}: {e}")
                continue
        
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