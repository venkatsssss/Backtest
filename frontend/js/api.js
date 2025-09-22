// SageForge Backtesting Module - API Communication

class BacktestingAPI {
    constructor() {
        this.baseURL = CONFIG.API_BASE_URL;
    }

    async request(endpoint, options = {}) {
        try {
            const url = `${this.baseURL}${endpoint}`;
            const config = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                ...options
            };

            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();

        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    async get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    }

    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // BOX 1: Stocks API
    async getStocks(sector = 'all') {
        try {
            const endpoint = `${CONFIG.ENDPOINTS.GET_STOCKS}?sector=${sector}`;
            return await this.get(endpoint);
        } catch (error) {
            console.error('Error fetching stocks:', error);
            throw error;
        }
    }

    async getSectors() {
        try {
            return await this.get(CONFIG.ENDPOINTS.GET_SECTORS);
        } catch (error) {
            console.error('Error fetching sectors:', error);
            // Return default sectors as fallback
            return [
                { id: 'all', name: 'All Stocks' },
                { id: 'banking', name: 'Banking' },
                { id: 'it', name: 'Information Technology' },
                { id: 'pharma', name: 'Pharmaceuticals' },
                { id: 'fmcg', name: 'FMCG' }
            ];
        }
    }

    // BOX 2: Strategies API
    async getStrategyTypes() {
        try {
            return await this.get(CONFIG.ENDPOINTS.GET_STRATEGY_TYPES);
        } catch (error) {
            console.error('Error fetching strategy types:', error);
            return [
                {
                    id: "ema_crossover",
                    name: "EMA Crossover",
                    description: "Buy when 9-EMA crosses above 21-EMA",
                    category: "trend_following",
                    expected_win_rate: "45-55%",
                    risk_level: "medium"
                },
                {
                    id: "rsi_oversold",
                    name: "RSI Oversold Recovery", 
                    description: "Buy when RSI recovers from oversold levels",
                    category: "mean_reversion",
                    expected_win_rate: "60-70%",
                    risk_level: "medium"
                },
                {
                    id: "hammer_pattern",
                    name: "Hammer Pattern",
                    description: "Buy on hammer candlestick in downtrend",
                    category: "candlestick",
                    expected_win_rate: "65-75%",
                    risk_level: "high"
                }
            ];
        }
    }

    async getStrategyCategories() {
        try {
            return await this.get(CONFIG.ENDPOINTS.GET_STRATEGY_CATEGORIES);
        } catch (error) {
            console.error('Error fetching strategy categories:', error);
            return [
                { id: "trend_following", name: "Trend Following" },
                { id: "mean_reversion", name: "Mean Reversion" },
                { id: "candlestick", name: "Candlestick Patterns" }
            ];
        }
    }

    // BOX 3: Periods API
    async getPeriodPresets() {
        try {
            return await this.get(CONFIG.ENDPOINTS.GET_PERIOD_PRESETS);
        } catch (error) {
            console.error('Error fetching period presets:', error);
            const today = new Date();
            const formatDate = (date) => date.toISOString().split('T')[0];
            
            return [
                {
                    id: "1year",
                    name: "Last 1 Year",
                    start_date: formatDate(new Date(today.getFullYear() - 1, today.getMonth(), today.getDate())),
                    end_date: formatDate(today),
                    description: "Good for testing recent strategies"
                },
                {
                    id: "3years",
                    name: "Last 3 Years",
                    start_date: formatDate(new Date(today.getFullYear() - 3, today.getMonth(), today.getDate())),
                    end_date: formatDate(today),
                    description: "Includes market volatility and cycles"
                }
            ];
        }
    }

    // Backtesting API
    async runBacktest(backtestRequest) {
        try {
            return await this.post(CONFIG.ENDPOINTS.RUN_BACKTEST, backtestRequest);
        } catch (error) {
            console.error('Error starting backtest:', error);
            throw error;
        }
    }

    async getBacktestStatus(backtestId) {
        try {
            const endpoint = CONFIG.ENDPOINTS.GET_BACKTEST_STATUS.replace('{id}', backtestId);
            return await this.get(endpoint);
        } catch (error) {
            console.error('Error getting backtest status:', error);
            throw error;
        }
    }

    async getBacktestResult(backtestId) {
        try {
            const endpoint = CONFIG.ENDPOINTS.GET_BACKTEST_RESULT.replace('{id}', backtestId);
            return await this.get(endpoint);
        } catch (error) {
            console.error('Error getting backtest result:', error);
            throw error;
        }
    }

    async healthCheck() {
        try {
            return await this.get(CONFIG.ENDPOINTS.HEALTH_CHECK);
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'unhealthy' };
        }
    }

    // Polling for backtest status
    async pollBacktestStatus(backtestId, onUpdate) {
        const poll = async () => {
            try {
                const status = await this.getBacktestStatus(backtestId);
                onUpdate(status);

                if (status.status === 'running') {
                    setTimeout(poll, CONFIG.UI.BACKTEST_STATUS_POLL_INTERVAL);
                }
            } catch (error) {
                console.error('Polling error:', error);
                onUpdate({ status: 'failed', message: error.message });
            }
        };

        poll();
    }
}

// Create global API instance
const api = new BacktestingAPI();

