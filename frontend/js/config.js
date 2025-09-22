// SageForge Backtesting Module - Configuration

const CONFIG = {
    API_BASE_URL: 'http://127.0.0.1:8000/api'
,
    
    ENDPOINTS: {
        GET_STOCKS: '/stocks',
        GET_SECTORS: '/stocks/sectors',
        GET_STRATEGY_TYPES: '/strategies/types',
        GET_STRATEGY_CATEGORIES: '/strategies/categories',
        GET_PERIOD_PRESETS: '/periods/presets',
        RUN_BACKTEST: '/backtest/run',
        GET_BACKTEST_STATUS: '/backtest/{id}/status',
        GET_BACKTEST_RESULT: '/backtest/{id}/result',
        HEALTH_CHECK: '/health',
        RUN_HAMMER_BACKTEST: '/backtest/hammer'
    },
    
    UI: {
        BACKTEST_STATUS_POLL_INTERVAL: 2000,
        MIN_STOCKS_SELECTION: 1,
        MAX_STOCKS_SELECTION: 20,
        
        CHART_COLORS: {
            primary: '#dc2626',
            success: '#059669',
            warning: '#d97706',
            danger: '#dc2626',
            info: '#0891b2',
            secondary: '#6b7280',
            background: '#1f1f1f',
            grid: '#374151'
        }
    },
    
    TRADING: {
        DEFAULT_INITIAL_CAPITAL: 100000,
        COMMISSION_RATE: 0.0003,
        SLIPPAGE_RATE: 0.001,
        DEFAULT_STOP_LOSS: 2.0,
        DEFAULT_TAKE_PROFIT: 5.0
    },
    
    UTILS: {
        formatCurrency: (amount) => {
            return new Intl.NumberFormat('en-IN', {
                style: 'currency',
                currency: 'INR',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(amount);
        },
        
        formatPercentage: (value, decimals = 2) => {
            return `${value.toFixed(decimals)}%`;
        },
        
        formatDate: (date) => {
            return new Intl.DateTimeFormat('en-IN').format(new Date(date));
        },
        
        formatNumber: (number, decimals = 2) => {
            return new Intl.NumberFormat('en-IN', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }).format(number);
        },
        
        debounce: (func, wait) => {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    }
};

window.CONFIG = CONFIG;

