# SageForge Backtesting Module

A complete backtesting simulator for Indian stock market trading strategies with real-time data integration.

## 🚀 Features

### Three-Box Interface
- **Box 1**: NSE Stock Selection with sector filtering
- **Box 2**: Strategy Selection (EMA Crossover, RSI, Candlestick Patterns)  
- **Box 3**: Period Selection with presets and custom dates

### Advanced Backtesting
- **Technical Indicators**: SMA, EMA, RSI, MACD, Bollinger Bands
- **Candlestick Patterns**: Hammer, Doji, Engulfing, Morning Star
- **Realistic Trading**: Transaction costs, slippage modeling
- **Professional Metrics**: Sharpe ratio, max drawdown, win rate

## 🛠 Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Backend**: Python FastAPI with Angel One SmartAPI
- **Charts**: Chart.js for visualizations
- **Design**: SageForge red/black/silver theme

## 📁 Project Structure

```
sageforge_backtesting/
├── requirements.txt          # Python dependencies
├── .env                      # API configuration
├── README.md                 # This file
├── start.sh                  # Startup script
├── backend/                  # Python backend
│   ├── config.py            # Settings
│   ├── main.py              # FastAPI server
│   ├── models/
│   │   └── database.py      # Data models
│   └── services/
│       ├── angel_one_service.py  # API integration
│       └── backtest_engine.py    # Core engine
└── frontend/                # Web interface
    ├── index.html           # Main page
    ├── css/
    │   ├── styles.css       # Main styles
    │   └── responsive.css   # Mobile styles
    └── js/
        ├── config.js        # Configuration
        ├── api.js           # API communication  
        └── main.js          # Application logic
```

## 🚀 Quick Start

### Method 1: One-Click Start (Recommended)
```bash
# Make startup script executable
chmod +x start.sh

# Run the application
./start.sh
```

### Method 2: Manual Setup
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Configure Angel One API (optional for demo)
# Edit .env file with your credentials

# 3. Start backend server
cd backend
python main.py

# 4. Start frontend server (new terminal)
cd frontend  
python -m http.server 3000

# 5. Open browser
# Go to: http://localhost:3000
```

## 📖 How to Use

### Step 1: Select Stocks (Box 1)
- Search for stocks: "TCS", "RELIANCE", "INFY"
- Filter by sector: Banking, IT, Pharma
- Select up to 20 stocks

### Step 2: Choose Strategy (Box 2)  
- **EMA Crossover**: 9-EMA crosses 21-EMA
- **RSI Oversold**: Buy when RSI recovers from <30
- **Hammer Pattern**: Bullish reversal candlestick
- **Engulfing Pattern**: Bullish engulfing candle

### Step 3: Select Period (Box 3)
- **Quick presets**: Last 1 Year, 3 Years, 5 Years
- **Custom dates**: Pick your own range
- Minimum 30 days recommended

### Step 4: Run Backtest
- Click "Start Backtesting" button
- Watch real-time progress
- Results appear automatically (30-60 seconds)

### Step 5: Analyze Results
- **Summary Cards**: Total return, win rate, Sharpe ratio
- **Equity Curve**: Portfolio growth over time
- **Trade Log**: Detailed trade history
- **Charts**: Interactive visualizations

## ⚙️ Configuration

### Angel One API Setup (Optional)
1. Create account at https://angelone.in
2. Apply for SmartAPI access
3. Update `.env` file:
```env
ANGEL_ONE_API_KEY=your_api_key
ANGEL_ONE_CLIENT_ID=your_client_id
ANGEL_ONE_PASSWORD=your_password
```

### Demo Mode
- Works without API credentials
- Uses simulated data for testing
- Perfect for development and learning

## 📊 Performance Metrics

### Returns
- **Total Return**: Overall portfolio performance
- **Annual Return**: Annualized percentage return
- **Sharpe Ratio**: Risk-adjusted returns (>1.5 good, >2.0 excellent)

### Risk Metrics  
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Total Trades**: Number of trades executed

## 🎨 Design Features

- **SageForge Theme**: Professional red/black/silver colors
- **Responsive Design**: Works on mobile, tablet, desktop
- **Dark Mode**: Easy on the eyes for long analysis sessions
- **Interactive Charts**: Hover for detailed information
- **Smooth Animations**: Polished user experience

## 🔧 Troubleshooting

### Common Issues

**"Module not found" error:**
```bash
pip install -r requirements.txt
```

**"Port already in use" error:**
```bash
# Kill existing processes
pkill -f python
pkill -f "http.server"
```

**"CORS error" in browser:**
- Ensure both backend (port 8000) and frontend (port 3000) are running
- Check browser console for specific errors

**No data appearing:**
- Check if backend server is running at http://localhost:8000
- Visit http://localhost:8000/docs to test API directly

### Getting Help

1. **Check browser console** for JavaScript errors
2. **Check terminal** for Python errors  
3. **Test API health** at http://localhost:8000/api/health
4. **Restart both servers** if issues persist

## 🚀 Advanced Usage

### Adding New Strategies
Edit `backend/services/backtest_engine.py`:
```python
def _check_your_strategy_entry(self, row, index, data):
    # Your custom strategy logic here
    return True  # Buy signal
```

### Customizing UI
Edit `frontend/css/styles.css`:
```css
:root {
    --primary-red: #your-color;  # Change theme colors
}
```

### Performance Optimization
- Use fewer stocks for faster backtesting
- Shorter time periods reduce processing time
- Close other browser tabs to free memory

## 📈 Strategy Recommendations

### For Beginners
- Start with "EMA Crossover" strategy
- Test on 3-5 large-cap stocks (TCS, RELIANCE)
- Use 1-year period for quick results

### For Advanced Users
- Experiment with candlestick patterns
- Test across different market conditions
- Compare multiple strategies side-by-side

### Best Practices
- Always include transaction costs
- Test strategies across different time periods
- Don't over-optimize based on past data
- Paper trade before live implementation

## 🎯 Future Enhancements

- [ ] Multi-timeframe analysis
- [ ] Portfolio optimization
- [ ] Options strategies
- [ ] Real-time alerts
- [ ] Social sharing features
- [ ] Mobile app version

## 📄 License

This project is for educational and research purposes.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Test thoroughly
4. Submit pull request

---

**Built with ❤️ for Indian traders**

*Happy Trading! 📈*
