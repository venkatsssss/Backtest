import os
import logging
from datetime import datetime, timedelta
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import Config
from .models.schemas import (
    BacktestRequest, BacktestResponse, StockInfo, HealthResponse
)
from .service.angel_one_service import AngelOneService
from .service.backtest_engine import BacktestEngine
from .utils.excel_export import ExcelExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="SageForge Backtesting API",
    description="Hammer Pattern Backtesting for NSE Stocks",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
angel_service = AngelOneService()
backtest_engine = BacktestEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting SageForge API...")
    try:
        success = await angel_service.authenticate()
        if success:
            logger.info("✅ Angel One API connected")
        else:
            logger.warning("⚠️ Angel One authentication failed")
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down SageForge API...")
    try:
        angel_service.logout()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SageForge Backtesting API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if angel_service.is_authenticated else "limited",
        angel_one_connected=angel_service.is_authenticated,
        timestamp=datetime.now().isoformat()
    )

@app.get("/api/stocks", response_model=List[StockInfo])
async def get_stocks(sector: str = "all"):
    """
    Get NSE stocks list
    
    Query params:
    - sector: Filter by sector (all, banking, it, fmcg, pharma, auto, oil_gas)
    """
    try:
        stocks = await angel_service.get_nse_stocks(sector)
        return stocks
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sectors")
async def get_sectors():
    """Get available stock sectors"""
    return [
        {"id": "all", "name": "All Stocks"},
        {"id": "banking", "name": "Banking"},
        {"id": "it", "name": "Information Technology"},
        {"id": "fmcg", "name": "FMCG"},
        {"id": "pharma", "name": "Pharmaceuticals"},
        {"id": "auto", "name": "Automobiles"},
        {"id": "oil_gas", "name": "Oil & Gas"}
    ]

@app.get("/api/strategies")
async def get_strategies():
    """Get available trading strategies"""
    return [
        {
            "id": "hammer",
            "name": "Hammer Pattern",
            "description": "Bullish reversal with long lower shadow"
        },
        {
            "id": "inverted_hammer",
            "name": "Inverted Hammer",
            "description": "Potential reversal with long upper shadow"
        }
    ]

@app.post("/api/backtest")
async def run_backtest(request: BacktestRequest):
    """
    Run backtest analysis
    
    Request body:
    - stocks: List of stock symbols
    - strategy: 'hammer' or 'inverted_hammer'
    - target_percent: Target profit percentage (0.1-50)
    - stop_loss_percent: Stop loss percentage (0.1-20)
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - timeframe: Candle timeframe (default: 15min)
    """
    try:
        logger.info(f"🔨 Starting {request.strategy} backtest for {len(request.stocks)} stocks")
        
        # Validate inputs
        if not request.stocks:
            raise HTTPException(status_code=400, detail="No stocks selected")
        
        if not angel_service.is_authenticated:
            raise HTTPException(
                status_code=503,
                detail="Angel One API not connected. Please check credentials."
            )
        
        # Get historical data for all stocks
        interval = Config.TIMEFRAME_MAP.get(request.timeframe, Config.DEFAULT_TIMEFRAME)
        
        historical_data = await angel_service.get_multiple_historical_data(
            symbols=request.stocks,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=interval
        )
        
        if not historical_data:
            raise HTTPException(
                status_code=404,
                detail="No historical data available for selected stocks"
            )
        
        logger.info(f"Retrieved data for {len(historical_data)} stocks")
        
        # Run backtest
        results = await backtest_engine.run_backtest(
            historical_data=historical_data,
            strategy=request.strategy,
            target_percent=request.target_percent,
            stop_loss_percent=request.stop_loss_percent
        )
        
        # Add metadata
        results['strategy'] = request.strategy.replace('_', ' ').title()
        results['period'] = f"{request.start_date} to {request.end_date}"
        results['stocks_analyzed'] = len(request.stocks)
        results['timeframe'] = request.timeframe
        
        logger.info(f"✅ Backtest completed: {results['total_patterns']} patterns analyzed")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")

@app.post("/api/backtest/download")
async def download_backtest_excel(request: BacktestRequest):
    """
    Download backtest results as Excel file
    
    Same parameters as /api/backtest endpoint
    Returns Excel file for download
    """
    try:
        logger.info(f"Generating Excel report for {len(request.stocks)} stocks")
        
        # Run backtest (reuse logic)
        if not angel_service.is_authenticated:
            raise HTTPException(
                status_code=503,
                detail="Angel One API not connected"
            )
        
        interval = Config.TIMEFRAME_MAP.get(request.timeframe, Config.DEFAULT_TIMEFRAME)
        
        historical_data = await angel_service.get_multiple_historical_data(
            symbols=request.stocks,
            start_date=request.start_date,
            end_date=request.end_date,
            interval=interval
        )
        
        if not historical_data:
            raise HTTPException(status_code=404, detail="No data available")
        
        results = await backtest_engine.run_backtest(
            historical_data=historical_data,
            strategy=request.strategy,
            target_percent=request.target_percent,
            stop_loss_percent=request.stop_loss_percent
        )
        
        # Prepare summary data
        summary_data = {
            'strategy': request.strategy.replace('_', ' ').title(),
            'period': f"{request.start_date} to {request.end_date}",
            'stocks_analyzed': len(request.stocks),
            'total_patterns': results['total_patterns'],
            'target_hit_count': results['target_hit_count'],
            'stop_loss_count': results['stop_loss_count'],
            'eod_exit_count': results['eod_exit_count'],
            'target_hit_rate': results['target_hit_rate'],
            'stop_loss_rate': results['stop_loss_rate'],
            'avg_return': results['avg_return'],
            'total_points_gained': results['total_points_gained']
        }
        
        # Generate Excel file
        excel_file = ExcelExporter.create_excel_report(
            trades_data=results['trades'],
            summary_data=summary_data
        )
        
        # Prepare filename
        filename = f"backtest_{request.strategy}_{request.start_date}_to_{request.end_date}.xlsx"
        
        logger.info(f"✅ Excel report generated: {filename}")
        
        # Return as downloadable file
        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Excel generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Excel generation failed: {str(e)}")

# Mount static files (frontend)
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# Run server
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )