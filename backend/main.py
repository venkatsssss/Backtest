from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime, timedelta
import logging
import random
from fastapi.staticfiles import StaticFiles
 # Changed import


from .services.angel_one_service import angel_one_service
from .services.backtest_engine import RealDataBacktestEngine 


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="SageForge Backtesting API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize Angel One connection on startup - STRICT AUTHENTICATION REQUIRED"""
    try:
        logger.info("🔄 Attempting Angel One API authentication...")
        success = await angel_one_service.authenticate()
        if success:
            logger.info("✅ Angel One API connected successfully - REAL DATA AVAILABLE")
        else:
            logger.error("❌ Angel One API authentication FAILED - NO REAL DATA AVAILABLE")
            logger.error("❌ Please check your Angel One credentials in .env file")
            logger.error("❌ Required: ANGEL_ONE_API_KEY, ANGEL_ONE_CLIENT_ID, ANGEL_ONE_PASSWORD, ANGEL_ONE_TOTP_SECRET")
    except Exception as e:
        logger.error(f"❌ Startup error: {str(e)}")
        logger.error("❌ Angel One API authentication failed - REAL DATA NOT AVAILABLE")

@app.get("/")
async def root():
    return {"message": "SageForge Backtesting API", "status": "running"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy" if angel_one_service.is_authenticated else "no_real_data",
        "timestamp": datetime.now(),
        "angel_one_connected": angel_one_service.is_authenticated,
        "data_source": "Angel One Real API" if angel_one_service.is_authenticated else "NO REAL DATA",
        "warning": "Angel One API authentication required for real data" if not angel_one_service.is_authenticated else None
    }

@app.get("/api/stocks")
async def get_stocks(sector: str = "all"):
    """Get REAL NSE stocks from Angel One API ONLY"""
    try:
        # STRICT CHECK: Must be authenticated
        if not angel_one_service.is_authenticated:
            raise HTTPException(
                status_code=503, 
                detail="Angel One API not authenticated. Cannot provide real stock data. Please check your credentials."
            )
        
        stocks = await angel_one_service.get_nse_stocks(sector)
        
        if not stocks:
            raise HTTPException(
                status_code=404,
                detail="No real stock data available from Angel One API"
            )
        
        logger.info(f"✅ Retrieved {len(stocks)} REAL stocks from Angel One API for sector: {sector}")
        return stocks
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting real stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get real stocks from Angel One API: {str(e)}")
# ... (keep all other endpoints the same)

class BacktestRequest(BaseModel):
    symbols: List[str]
    strategy_type: str
    start_date: str
    end_date: str
    initial_capital: Optional[float] = 100000

class HammerBacktestRequest(BaseModel):
    stocks: List[str]
    strategy: str  # "hammer" or "inverted_hammer"
    target_percent: float
    stop_loss_percent: float
    start_date: str
    end_date: str
    timeframe: str = "15min"


active_backtests = {}

@app.post("/api/backtest/run")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Run backtest with REAL Angel One data ONLY"""
    try:
        # STRICT CHECK: Must be authenticated
        if not angel_one_service.is_authenticated:
            raise HTTPException(
                status_code=503,
                detail="Angel One API not authenticated. Cannot run backtest without real data. Please check your credentials."
            )
        
        backtest_id = f"real_bt_{int(datetime.now().timestamp())}"
        
        logger.info(f"🚀 Starting REAL DATA ONLY backtest {backtest_id} for {len(request.symbols)} stocks")
        
        active_backtests[backtest_id] = {
            "status": "running",
            "progress": 0,
            "message": "Authenticating with Angel One API...",
            "data_source": "Angel One Real API"
        }
        
        background_tasks.add_task(
            run_real_data_backtest_background,
            backtest_id,
            request
        )
        
        return {
            "backtest_id": backtest_id,
            "status": "started",
            "message": "REAL DATA backtest started with Angel One API",
            "data_source": "Angel One Real API"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error starting real data backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start real data backtest: {str(e)}")

async def run_real_data_backtest_background(backtest_id: str, request: BacktestRequest):
    """Background task for REAL DATA backtest ONLY"""
    try:
        # Double-check authentication
        if not angel_one_service.is_authenticated:
            active_backtests[backtest_id] = {
                "status": "failed",
                "progress": 0,
                "message": "Angel One API not authenticated - cannot proceed with real data backtest"
            }
            return
        
        # Update progress
        active_backtests[backtest_id]["message"] = "Fetching REAL historical data from Angel One API..."
        active_backtests[backtest_id]["progress"] = 20
        
        # Get REAL historical data ONLY
        historical_data = await angel_one_service.get_multiple_historical_data(
            request.symbols,
            request.start_date,
            request.end_date
        )
        
        active_backtests[backtest_id]["message"] = "Analyzing REAL market data patterns..."
        active_backtests[backtest_id]["progress"] = 60
        
        if not historical_data:
            raise Exception("No REAL historical data available from Angel One API for selected stocks")
        
        # Process real data (implement your strategy logic here)
        total_trades = 0
        winning_trades = 0
        trades = []
        
        for symbol, data in historical_data.items():
            if data.empty:
                continue
                
            # Detect real patterns
            patterns = angel_one_service.detect_hammer_patterns(data, "hammer")
            
            for pattern in patterns:
                # Create trade from real pattern
                trades.append({
                    "symbol": symbol,
                    "entry_date": pattern['timestamp'].strftime("%Y-%m-%d %H:%M"),
                    "exit_date": pattern['timestamp'].strftime("%Y-%m-%d %H:%M"),
                    "entry_price": pattern['entry_price'],
                    "exit_price": pattern['entry_price'],  # Simplified for demo
                    "quantity": 10,
                    "pnl": 0,  # Calculate based on your strategy
                    "confidence": pattern['confidence'],
                    "data_source": "Angel One Real API"
                })
                total_trades += 1
        
        total_pnl = sum(t["pnl"] for t in trades)
        total_return = (total_pnl / request.initial_capital) * 100
        
        result = {
            "final_capital": request.initial_capital + total_pnl,
            "total_return": round(total_return, 2),
            "total_trades": total_trades,
            "win_rate": round((winning_trades / max(total_trades, 1)) * 100, 2),
            "trades": trades,
            "data_source": "Angel One Real API",
            "stocks_processed": len(historical_data),
            "authentication_confirmed": True,
            "fake_data_used": False
        }
        
        active_backtests[backtest_id] = {
            "status": "completed",
            "progress": 100,
            "message": "REAL DATA backtest completed successfully",
            "result": result
        }
        
        logger.info(f"✅ REAL DATA backtest {backtest_id} completed with {total_trades} trades")
        
    except Exception as e:
        logger.error(f"❌ REAL DATA backtest {backtest_id} failed: {str(e)}")
        active_backtests[backtest_id] = {
            "status": "failed",
            "progress": 0,
            "message": f"REAL DATA backtest failed: {str(e)}"
        }

@app.post("/api/backtest/hammer")
async def run_hammer_backtest(request: HammerBacktestRequest):
    """Run hammer pattern backtest with REAL data ONLY"""
    try:
        if not angel_one_service.is_authenticated:
            raise HTTPException(
                status_code=503,
                detail="Angel One API not authenticated. Cannot run hammer backtest without real data."
            )
        
        logger.info(f"🔨 Starting REAL DATA {request.strategy} backtest for {len(request.stocks)} stocks")
        
        # Use the new RealDataBacktestEngine
        backtest_engine = RealDataBacktestEngine()
        results = await backtest_engine.run_hammer_analysis(
            stocks=request.stocks,
            strategy=request.strategy,
            target_percent=request.target_percent,
            stop_loss_percent=request.stop_loss_percent,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        results['data_source'] = 'Angel One Real API'
        results['authentication_status'] = 'Authenticated'
        results['fake_data_used'] = False
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Real hammer backtest error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Real data backtest failed: {str(e)}")


@app.get("/api/stocks/sectors")
async def get_sectors():
    return [
        {"id": "all", "name": "All Stocks"},
        {"id": "banking", "name": "Banking"},
        {"id": "it", "name": "Information Technology"},
        {"id": "fmcg", "name": "FMCG"},
        {"id": "oil_gas", "name": "Oil & Gas"},
        {"id": "pharma", "name": "Pharmaceuticals"},
        {"id": "telecom", "name": "Telecommunications"},
        {"id": "consumer", "name": "Consumer Goods"}
    ]

@app.get("/api/auth/check")
async def check_authentication():
    """Check Angel One API authentication status"""
    return {
        "authenticated": angel_one_service.is_authenticated,
        "status": "Connected to Angel One API" if angel_one_service.is_authenticated else "Not authenticated",
        "can_get_real_data": angel_one_service.is_authenticated,
        "message": "Ready for real data analysis" if angel_one_service.is_authenticated else "Please check Angel One credentials"
    }

@app.get("/api/strategies/types")
async def get_strategy_types():
    return [
        {
            "id": "ema_crossover",
            "name": "EMA Crossover",
            "description": "Buy when 9-EMA crosses above 21-EMA",
            "category": "trend_following",
            "expected_win_rate": "45-55%",
            "risk_level": "medium"
        },
        {
            "id": "rsi_oversold",
            "name": "RSI Oversold Recovery",
            "description": "Buy when RSI recovers from oversold levels",
            "category": "mean_reversion",
            "expected_win_rate": "60-70%",
            "risk_level": "medium"
        },
        {
            "id": "hammer_pattern",
            "name": "Hammer Pattern",
            "description": "Buy on hammer candlestick in downtrend",
            "category": "candlestick",
            "expected_win_rate": "65-75%",
            "risk_level": "high"
        },
        {
            "id": "engulfing_pattern",
            "name": "Bullish Engulfing",
            "description": "Buy on bullish engulfing pattern",
            "category": "candlestick",
            "expected_win_rate": "70-80%",
            "risk_level": "high"
        }
    ]

@app.get("/api/strategies/categories")
async def get_strategy_categories():
    return [
        {"id": "trend_following", "name": "Trend Following", "description": "Follow market trends"},
        {"id": "mean_reversion", "name": "Mean Reversion", "description": "Price returns to average"},
        {"id": "candlestick", "name": "Candlestick Patterns", "description": "Pattern recognition"}
    ]

@app.get("/api/periods/presets")
async def get_period_presets():
    today = datetime.now()
    return [
        {
            "id": "1year",
            "name": "Last 1 Year",
            "start_date": (today - timedelta(days=365)).strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": "Good for testing recent strategies"
        },
        {
            "id": "3years",
            "name": "Last 3 Years",
            "start_date": (today - timedelta(days=1095)).strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": "Includes market volatility and cycles"
        },
        {
            "id": "5years",
            "name": "Last 5 Years",
            "start_date": (today - timedelta(days=1825)).strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d"),
            "description": "Long-term strategy validation"
        }
    ]

# Fix the backtest status endpoint:
@app.get("/api/backtest/{backtest_id}/status")
async def get_backtest_status(backtest_id: str):
    if backtest_id not in active_backtests:
        raise HTTPException(status_code=404, detail="Backtest not found")
    return active_backtests[backtest_id]

@app.get("/api/backtest/{backtest_id}/result")
async def get_backtest_result(backtest_id: str):
    if backtest_id not in active_backtests:
        raise HTTPException(status_code=404, detail="Backtest not found")
    
    backtest_info = active_backtests[backtest_id]
    if backtest_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="Backtest not completed yet")
    
    return backtest_info["result"]
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
