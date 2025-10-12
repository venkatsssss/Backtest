# SageForge Backtesting Module - Database Models

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class StrategyType(str, Enum):
    EMA_CROSSOVER = "ema_crossover"
    RSI_OVERSOLD = "rsi_oversold"
    MACD_SIGNAL = "macd_signal"
    HAMMER_PATTERN = "hammer_pattern"
    ENGULFING_PATTERN = "engulfing_pattern"
    MORNING_STAR = "morning_star"
    CUSTOM = "custom"

class TimeFrame(str, Enum):
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    HOUR_1 = "1h"
    DAY_1 = "1d"

class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"

class Indicator(BaseModel):
    type: str = Field(..., description="Indicator type (EMA, SMA, RSI, etc.)")
    params: Dict[str, Any] = Field(..., description="Indicator parameters")

class Strategy(BaseModel):
    id: Optional[str] = Field(default=None, description="Strategy unique ID")
    name: str = Field(..., description="Strategy name")
    user_id: str = Field(..., description="User who created the strategy")
    type: StrategyType = Field(..., description="Strategy type")
    description: Optional[str] = Field(default=None, description="Strategy description")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

class Trade(BaseModel):
    entry_date: datetime = Field(..., description="Trade entry date")
    exit_date: Optional[datetime] = Field(default=None, description="Trade exit date")
    symbol: str = Field(..., description="Stock symbol")
    entry_price: float = Field(..., description="Entry price")
    exit_price: Optional[float] = Field(default=None, description="Exit price")
    quantity: int = Field(..., description="Number of shares")
    pnl: Optional[float] = Field(default=None, description="Profit/Loss")

class BacktestResult(BaseModel):
    id: Optional[str] = Field(default=None, description="Result unique ID")
    strategy_id: str = Field(..., description="Strategy ID that was tested")
    user_id: str = Field(..., description="User who ran the backtest")
    symbols: List[str] = Field(..., description="Stocks tested")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    initial_capital: float = Field(..., description="Starting capital")
    final_capital: float = Field(..., description="Final portfolio value")
    total_return: float = Field(..., description="Total return percentage")
    sharpe_ratio: float = Field(..., description="Risk-adjusted return")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    total_trades: int = Field(..., description="Total number of trades")
    win_rate: float = Field(..., description="Percentage of winning trades")
    trades: List[Trade] = Field(default=[], description="All trades executed")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Stock(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    name: str = Field(..., description="Company name")
    sector: str = Field(..., description="Industry sector")
    exchange: Exchange = Field(..., description="Stock exchange")
    is_active: bool = Field(default=True, description="Is stock actively traded")

class BacktestRequest(BaseModel):
    symbols: List[str] = Field(..., description="Stock symbols to test")
    strategy_type: str = Field(..., description="Strategy type to test")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(default=100000, description="Starting capital")


