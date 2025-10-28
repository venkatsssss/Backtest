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
        Detect Hammer pattern - RELAXED CRITERIA:
        - Lower shadow significantly longer than upper shadow
        - Lower shadow at least 1.5x body size
        - Small to medium body
        - Returns hammer candle timestamp (not next candle)
        """
        patterns = []
        
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
                
                # RELAXED Hammer criteria:
                # 1. Lower shadow must be longer than upper shadow
                # 2. Lower shadow >= 1.5x body (reduced from 2x)
                # 3. Upper shadow <= body (more lenient)
                # 4. Body should be at least 5% of range (not too small)
                # 5. Lower shadow should be meaningful (>= 1 point)
                
                if body == 0:  # Doji - skip
                    continue
                
                lower_shadow_ratio = lower_shadow / body
                upper_shadow_ratio = upper_shadow / body
                body_ratio = body / total_range
                
                # More lenient hammer detection
                is_hammer = (
                    lower_shadow > upper_shadow and  # Lower shadow dominant
                    lower_shadow_ratio >= 1.5 and     # Lower shadow >= 1.5x body (relaxed)
                    upper_shadow_ratio <= 1.0 and     # Upper shadow <= body (more lenient)
                    body_ratio >= 0.05 and            # Body >= 5% of range (relaxed)
                    lower_shadow >= 1.0               # Absolute minimum shadow (1 point)
                )
                
                if is_hammer:
                    # Get NEXT candle for entry price
                    next_candle = df.iloc[i + 1]
                    entry_price = float(next_candle['open'])
                    
                    # Store pattern with HAMMER timestamp (not entry timestamp)
                    patterns.append({
                        'timestamp': timestamp,  # HAMMER candle timestamp
                        'entry_timestamp': df.index[i + 1],  # Next candle for entry
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'close': close_price,
                        'entry_price': entry_price,  # Entry at next candle's open
                        'pattern_type': 'hammer',
                        'lower_shadow': round(lower_shadow, 2),
                        'upper_shadow': round(upper_shadow, 2),
                        'body_size': round(body, 2),
                        'total_range': round(total_range, 2),
                        'lower_shadow_ratio': round(lower_shadow_ratio, 2),
                        'upper_shadow_ratio': round(upper_shadow_ratio, 2),
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
        Detect Inverted Hammer pattern - RELAXED CRITERIA:
        - Upper shadow significantly longer than lower shadow
        - Upper shadow at least 1.5x body size
        - Small to medium body
        """
        patterns = []
        
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
                
                if total_range == 0 or total_range < 0.01:
                    continue
                
                lower_shadow = min(open_price, close_price) - low_price
                upper_shadow = high_price - max(open_price, close_price)
                
                if body == 0:  # Doji
                    continue
                
                upper_shadow_ratio = upper_shadow / body
                lower_shadow_ratio = lower_shadow / body
                body_ratio = body / total_range
                
                # Relaxed inverted hammer criteria
                is_inverted_hammer = (
                    upper_shadow > lower_shadow and   # Upper shadow dominant
                    upper_shadow_ratio >= 1.5 and     # Upper shadow >= 1.5x body
                    lower_shadow_ratio <= 1.0 and     # Lower shadow <= body
                    body_ratio >= 0.05 and            # Body >= 5% of range
                    upper_shadow >= 1.0               # Absolute minimum shadow
                )
                
                if is_inverted_hammer:
                    # Get NEXT candle for entry
                    next_candle = df.iloc[i + 1]
                    entry_price = float(next_candle['open'])
                    
                    patterns.append({
                        'timestamp': timestamp,  # INVERTED HAMMER timestamp
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
        confidence = 40.0  # Base confidence
        
        # Main shadow dominance (more weight for stronger shadows)
        if shadow_ratio >= 3.0:
            confidence += 35
        elif shadow_ratio >= 2.0:
            confidence += 25
        elif shadow_ratio >= 1.5:
            confidence += 15
        else:
            confidence += 5
        
        # Opposite shadow minimality
        if opposite_shadow <= 0.5:
            confidence += 15
        elif opposite_shadow <= 1.0:
            confidence += 10
        else:
            confidence += 5
        
        # Body significance
        if body_ratio >= 0.15:
            confidence += 10
        elif body_ratio >= 0.10:
            confidence += 5
        
        return min(confidence, 100.0)