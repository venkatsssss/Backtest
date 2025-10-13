// Main Application
class SageForgeApp {
    constructor() {
        this.state = {
            allStocks: [],
            filteredStocks: [],
            selectedStocks: [],
            selectedStrategy: 'hammer',
            selectedPeriodMonths: 1,
            isCustomPeriod: false,
            lastBacktestParams: null
        };

        this.api = window.apiService;
        this.ui = window.uiHandler;
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing SageForge...');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Check API health
        await this.checkHealth();
        
        // Load stocks
        await this.loadStocks();
        
        // Set date limits
        this.setDateLimits();
        
        // Update button state
        this.updateStartButton();
        
        console.log('✅ SageForge initialized');
    }

    async checkHealth() {
        try {
            const health = await this.api.checkHealth();
            this.ui.updateStatus(health.status, health.angel_one_connected);
        } catch (error) {
            console.error('Health check failed:', error);
            this.ui.updateStatus('error', false);
        }
    }

    async loadStocks(sector = 'all') {
        try {
            this.ui.showLoading(document.getElementById('stockList'));
            const stocks = await this.api.getStocks(sector);
            this.state.allStocks = stocks;
            this.state.filteredStocks = stocks;
            this.ui.renderStocks(this.state.filteredStocks, this.state.selectedStocks);
            console.log(`✅ Loaded ${stocks.length} stocks`);
        } catch (error) {
            console.error('Failed to load stocks:', error);
            this.ui.showError('Failed to load stocks. Using demo data.');
        }
    }

    setupEventListeners() {
        // Sector tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.loadStocks(e.target.dataset.sector);
            });
        });

        // Stock search
        document.getElementById('stockSearch').addEventListener('input', (e) => {
            this.searchStocks(e.target.value);
        });

        // Select/Clear buttons
        document.getElementById('selectAllBtn').addEventListener('click', () => {
            this.selectAllStocks();
        });

        document.getElementById('clearAllBtn').addEventListener('click', () => {
            this.clearAllStocks();
        });

        // Strategy cards
        document.querySelectorAll('.strategy-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const cardElement = e.currentTarget;
                document.querySelectorAll('.strategy-card').forEach(c => c.classList.remove('active'));
                cardElement.classList.add('active');
                this.state.selectedStrategy = cardElement.dataset.strategy;
                this.updateStartButton();
            });
        });

        // Period cards
        document.querySelectorAll('.period-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const cardElement = e.currentTarget;
                document.querySelectorAll('.period-card').forEach(c => c.classList.remove('active'));
                cardElement.classList.add('active');
                this.state.selectedPeriodMonths = parseInt(cardElement.dataset.months);
                this.state.isCustomPeriod = false;
                document.getElementById('customPeriodCheck').checked = false;
                document.getElementById('customDates').style.display = 'none';
                this.updateStartButton();
            });
        });

        // Custom period checkbox
        document.getElementById('customPeriodCheck').addEventListener('change', (e) => {
            this.state.isCustomPeriod = e.target.checked;
            document.getElementById('customDates').style.display = e.target.checked ? 'grid' : 'none';
            
            if (e.target.checked) {
                document.querySelectorAll('.period-card').forEach(c => c.classList.remove('active'));
            }
            
            this.updateStartButton();
        });

        // Date inputs
        ['startDate', 'endDate'].forEach(id => {
            document.getElementById(id).addEventListener('change', () => {
                this.validateDates();
                this.updateStartButton();
            });
        });

        // Parameter inputs
        ['targetPercent', 'stopLossPercent'].forEach(id => {
            document.getElementById(id).addEventListener('input', () => {
                this.updateStartButton();
            });
        });

        // Start backtest button
        document.getElementById('startBacktestBtn').addEventListener('click', () => {
            this.startBacktest();
        });

        // Download buttons
        document.getElementById('downloadExcelBtn').addEventListener('click', () => {
            this.downloadExcel();
        });

        document.getElementById('downloadJsonBtn').addEventListener('click', () => {
            this.downloadJSON();
        });
    }

    searchStocks(query) {
        if (!query.trim()) {
            this.state.filteredStocks = this.state.allStocks;
        } else {
            const lowerQuery = query.toLowerCase();
            this.state.filteredStocks = this.state.allStocks.filter(stock =>
                stock.symbol.toLowerCase().includes(lowerQuery) ||
                stock.name.toLowerCase().includes(lowerQuery)
            );
        }
        this.ui.renderStocks(this.state.filteredStocks, this.state.selectedStocks);
    }

    toggleStock(symbol) {
        const index = this.state.selectedStocks.indexOf(symbol);
        if (index === -1) {
            this.state.selectedStocks.push(symbol);
        } else {
            this.state.selectedStocks.splice(index, 1);
        }
        this.ui.updateSelectedCount(this.state.selectedStocks.length);
        this.updateStartButton();
    }

    selectAllStocks() {
        this.state.filteredStocks.forEach(stock => {
            if (!this.state.selectedStocks.includes(stock.symbol)) {
                this.state.selectedStocks.push(stock.symbol);
            }
        });
        this.ui.renderStocks(this.state.filteredStocks, this.state.selectedStocks);
        this.ui.updateSelectedCount(this.state.selectedStocks.length);
        this.updateStartButton();
    }

    clearAllStocks() {
        this.state.selectedStocks = [];
        this.ui.renderStocks(this.state.filteredStocks, this.state.selectedStocks);
        this.ui.updateSelectedCount(0);
        this.updateStartButton();
    }

    setDateLimits() {
        const today = new Date();
        const maxDate = today.toISOString().split('T')[0];
        const minDate = new Date(today.getTime() - (365 * 24 * 60 * 60 * 1000))
            .toISOString().split('T')[0];

        const startDateInput = document.getElementById('startDate');
        const endDateInput = document.getElementById('endDate');

        if (startDateInput) {
            startDateInput.max = maxDate;
            startDateInput.min = minDate;
        }

        if (endDateInput) {
            endDateInput.max = maxDate;
            endDateInput.min = minDate;
        }
    }

    validateDates() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;

        if (startDate && endDate) {
            if (new Date(startDate) >= new Date(endDate)) {
                alert('Start date must be before end date');
                document.getElementById('endDate').value = '';
            }
        }
    }

    updateStartButton() {
        const btn = document.getElementById('startBacktestBtn');
        
        const hasStocks = this.state.selectedStocks.length > 0;
        const hasTarget = parseFloat(document.getElementById('targetPercent').value) > 0;
        const hasStopLoss = parseFloat(document.getElementById('stopLossPercent').value) > 0;
        const hasValidPeriod = this.state.isCustomPeriod
            ? (document.getElementById('startDate').value && document.getElementById('endDate').value)
            : this.state.selectedPeriodMonths > 0;

        const isValid = hasStocks && hasTarget && hasStopLoss && hasValidPeriod;
        
        btn.disabled = !isValid;
    }

    getDateRange() {
        if (this.state.isCustomPeriod) {
            return {
                start_date: document.getElementById('startDate').value,
                end_date: document.getElementById('endDate').value
            };
        } else {
            const today = new Date();
            const daysMap = {
                1: 30,
                3: 90,
                6: 180,
                12: 365
            };
            
            const daysBack = daysMap[this.state.selectedPeriodMonths] || 30;
            const startDate = new Date(today);
            startDate.setDate(startDate.getDate() - daysBack);
            
            return {
                start_date: startDate.toISOString().split('T')[0],
                end_date: today.toISOString().split('T')[0]
            };
        }
    }

    async startBacktest() {
        try {
            console.log('🔨 Starting backtest...');
            
            const dateRange = this.getDateRange();
            
            const params = {
                stocks: this.state.selectedStocks,
                strategy: this.state.selectedStrategy,
                target_percent: parseFloat(document.getElementById('targetPercent').value),
                stop_loss_percent: parseFloat(document.getElementById('stopLossPercent').value),
                start_date: dateRange.start_date,
                end_date: dateRange.end_date,
                timeframe: '15min'
            };

            console.log('📊 Backtest parameters:', params);

            // Store params for downloads
            this.state.lastBacktestParams = params;

            // Show progress
            this.ui.showProgress();

            // Run backtest
            const results = await this.api.runBacktest(params);

            console.log('✅ Backtest completed:', results);

            // Display results
            this.ui.displayResults(results);

        } catch (error) {
            console.error('❌ Backtest failed:', error);
            this.ui.showError(error.message || 'Backtest failed. Please try again.');
        }
    }

    async downloadExcel() {
        try {
            if (!this.state.lastBacktestParams) {
                alert('Please run a backtest first');
                return;
            }

            console.log('📥 Downloading Excel report...');
            
            await this.api.downloadExcel(this.state.lastBacktestParams);
            
            console.log('✅ Excel downloaded successfully');
            
        } catch (error) {
            console.error('❌ Excel download failed:', error);
            alert('Failed to download Excel report: ' + error.message);
        }
    }

    downloadJSON() {
        try {
            if (!this.api.lastBacktestResults) {
                alert('Please run a backtest first');
                return;
            }

            console.log('📄 Downloading JSON data...');

            const params = this.state.lastBacktestParams;
            const filename = `backtest_${params.strategy}_${params.start_date}_to_${params.end_date}.json`;
            
            this.api.downloadJSON(this.api.lastBacktestResults, filename);
            
            console.log('✅ JSON downloaded successfully');
            
        } catch (error) {
            console.error('❌ JSON download failed:', error);
            alert('Failed to download JSON data: ' + error.message);
        }
    }
}

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.app = new SageForgeApp();
    });
} else {
    window.app = new SageForgeApp();
}