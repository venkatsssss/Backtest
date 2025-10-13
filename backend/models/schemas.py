from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class BacktestRequest(BaseModel):
    """Request model for backtesting"""
    stocks: List[str] = Field(..., description="List of stock symbols")
    strategy: str = Field(..., description="Strategy type: 'hammer' or 'inverted_hammer'")
    target_percent: float = Field(..., ge=0.1, le=50, description="Target profit percentage")
    stop_loss_percent: float = Field(..., ge=0.1, le=20, description="Stop loss percentage")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    timeframe: str = Field(default="15min", description="Candle timeframe")

class TradeResult(BaseModel):
    """Individual trade result"""
    stock: str
    pattern_date: str
    pattern_time: str
    entry_price: float
    target_price: float
    stop_loss_price: float
    exit_price: float
    exit_time: str
    exit_reason: str
    points_gained: float
    percentage_return: float
    minutes_held: int
    candles_held: int
    outcome: str  # 'target_hit', 'stop_loss', 'eod_exit'

class BacktestResponse(BaseModel):
    """Response model for backtest results"""
    total_patterns: int
    target_hit_count: int
    stop_loss_count: int
    eod_exit_count: int
    target_hit_rate: float
    stop_loss_rate: float
    avg_return: float
    total_points_gained: float
    trades: List[TradeResult]
    strategy: str
    period: str
    stocks_analyzed: int
    
class StockInfo(BaseModel):
    """Stock information model"""
    symbol: str
    name: str
    token: str
    exchange: str
    sector: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    angel_one_connected: bool
    timestamp: str