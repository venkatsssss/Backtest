"""SageForge Backtesting Backend"""
__version__ = "1.0.0"

# backend/service/__init__.py
from angel_one_service import AngelOneService
from backtest_engine import BacktestEngine

__all__ = ['AngelOneService', 'BacktestEngine']

# backend/models/__init__.py
from .schemas import (
    BacktestRequest,
    BacktestResponse,
    TradeResult,
    StockInfo,
    HealthResponse
)

__all__ = [
    'BacktestRequest',
    'BacktestResponse',
    'TradeResult',
    'StockInfo',
    'HealthResponse'
]

# backend/utils/__init__.py
from .pattern_detector import PatternDetector
from .excel_export import ExcelExporter

__all__ = ['PatternDetector', 'ExcelExporter']