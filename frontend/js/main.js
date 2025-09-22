// SageForge Hammer Pattern - Complete Working Version
class SageForgeApp {
    constructor() {
        this.selectedStocks = [];
        this.allStocks = [];
        this.filteredStocks = [];
        this.selectedStrategy = 'hammer';
        this.selectedPeriod = 1;
        this.isCustomPeriod = false;
        this.init();
    }

    async init() {
        try {
            console.log('🚀 Initializing SageForge...');
            this.setupEventListeners();
            await this.checkAPIHealth();
            await this.loadStocks();
            this.setDateLimits();
            this.updateStartButton();
            console.log('✅ SageForge initialized');
        } catch (error) {
            console.error('❌ Initialization error:', error);
        }
    }

    async checkAPIHealth() {
        try {
            const API_BASE = 'https://your-render-app-name.onrender.com/api';
            const health = await response.json();
            const statusElement = document.getElementById('marketStatus');
            if (health.status === 'healthy') {
                statusElement.innerHTML = `🟢 Connected`;
            } else {
                statusElement.innerHTML = `🟡 Demo Mode`;
            }
        } catch (error) {
            console.error('API health check failed:', error);
            const statusElement = document.getElementById('marketStatus');
            statusElement.innerHTML = `🔴 Connection Failed`;
        }
    }

    setupEventListeners() {
        // Sector tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const activeTab = document.querySelector('.tab-btn.active');
                if (activeTab) activeTab.classList.remove('active');
                e.target.classList.add('active');
                this.filterStocks(e.target.dataset.sector);
            });
        });

        // Stock search
        const stockSearch = document.getElementById('stockSearch');
        if (stockSearch) {
            stockSearch.addEventListener('input', (e) => {
                this.searchStocks(e.target.value);
            });
        }

        // Select all & clear buttons
        const selectAllBtn = document.getElementById('selectAll');
        const clearBtn = document.getElementById('clearStocks');
        
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                this.selectAllVisible();
            });
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearSelection();
            });
        }

        // Strategy selection
        document.querySelectorAll('.strategy-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const activeCard = document.querySelector('.strategy-card.active');
                if (activeCard) activeCard.classList.remove('active');
                card.classList.add('active');
                this.selectedStrategy = card.dataset.strategy;
                this.updateStartButton();
            });
        });

        // Period selection
        document.querySelectorAll('.period-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const activeCard = document.querySelector('.period-card.active');
                if (activeCard) activeCard.classList.remove('active');
                card.classList.add('active');
                this.selectedPeriod = parseInt(card.dataset.period);
                const customPeriod = document.getElementById('customPeriod');
                if (customPeriod) customPeriod.checked = false;
                this.isCustomPeriod = false;
                const customInputs = document.getElementById('customInputs');
                if (customInputs) customInputs.style.display = 'none';
                this.updateStartButton();
            });
        });

        // Custom period
        const customPeriodCheckbox = document.getElementById('customPeriod');
        if (customPeriodCheckbox) {
            customPeriodCheckbox.addEventListener('change', (e) => {
                this.isCustomPeriod = e.target.checked;
                const customInputs = document.getElementById('customInputs');
                if (customInputs) {
                    customInputs.style.display = e.target.checked ? 'flex' : 'none';
                }
                if (e.target.checked) {
                    const activeCard = document.querySelector('.period-card.active');
                    if (activeCard) activeCard.classList.remove('active');
                }
                this.updateStartButton();
            });
        }

        // Parameters
        const targetPercent = document.getElementById('targetPercent');
        const stopLossPercent = document.getElementById('stopLossPercent');
        
        if (targetPercent) {
            targetPercent.addEventListener('input', () => {
                this.updateStartButton();
            });
            targetPercent.addEventListener('keyup', () => {
                this.updateStartButton();
            });
        }
        
        if (stopLossPercent) {
            stopLossPercent.addEventListener('input', () => {
                this.updateStartButton();
            });
            stopLossPercent.addEventListener('keyup', () => {
                this.updateStartButton();
            });
        }

        // Date inputs
        const startDate = document.getElementById('startDate');
        const endDate = document.getElementById('endDate');
        
        if (startDate) {
            startDate.addEventListener('change', () => {
                this.validateDates();
            });
        }
        
        if (endDate) {
            endDate.addEventListener('change', () => {
                this.validateDates();
            });
        }

        // Start analysis button
        const startBtn = document.getElementById('startHammerAnalysis');
        if (startBtn) {
            startBtn.addEventListener('click', () => {
                this.startHammerAnalysis();
            });
        }
    }

    async loadStocks() {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/stocks?sector=all');
            if (!response.ok) throw new Error('Failed to load stocks');
            
            this.allStocks = await response.json();
            this.filteredStocks = [...this.allStocks];
            this.renderStocks();
            console.log(`✅ Loaded ${this.allStocks.length} stocks`);
        } catch (error) {
            console.error('Error loading stocks:', error);
            const stockList = document.getElementById('stockList');
            if (stockList) {
                stockList.innerHTML = `
                    <div class="error">❌ Failed to load stocks: ${error.message}</div>
                `;
            }
        }
    }

    renderStocks() {
        const stockList = document.getElementById('stockList');
        if (!stockList) return;

        if (this.filteredStocks.length === 0) {
            stockList.innerHTML = '<div class="loading">No stocks found</div>';
            return;
        }

        stockList.innerHTML = this.filteredStocks.slice(0, 50).map(stock => `
            <div class="stock-item">
                <input type="checkbox" value="${stock.symbol}" id="stock-${stock.symbol}" 
                       onchange="app.toggleStock('${stock.symbol}')">
                <div class="stock-info">
                    <div class="stock-symbol">${stock.symbol}</div>
                    <div class="stock-name">${stock.name}</div>
                    <div class="stock-sector">${stock.sector}</div>
                </div>
            </div>
        `).join('');

        this.updateStockCounter();
    }

    filterStocks(sector) {
        if (sector === 'all') {
            this.filteredStocks = [...this.allStocks];
        } else {
            this.filteredStocks = this.allStocks.filter(stock => 
                stock.sector.toLowerCase().includes(sector.toLowerCase())
            );
        }
        this.renderStocks();
    }

    searchStocks(query) {
        if (!query) {
            this.filteredStocks = [...this.allStocks];
        } else {
            this.filteredStocks = this.allStocks.filter(stock =>
                stock.symbol.toLowerCase().includes(query.toLowerCase()) ||
                stock.name.toLowerCase().includes(query.toLowerCase())
            );
        }
        this.renderStocks();
    }

    toggleStock(symbol) {
        if (this.selectedStocks.includes(symbol)) {
            this.selectedStocks = this.selectedStocks.filter(s => s !== symbol);
        } else {
            this.selectedStocks.push(symbol);
        }
        this.updateStockCounter();
        this.updateStartButton();
    }

    selectAllVisible() {
        this.filteredStocks.slice(0, 50).forEach(stock => {
            if (!this.selectedStocks.includes(stock.symbol)) {
                this.selectedStocks.push(stock.symbol);
            }
            const checkbox = document.getElementById(`stock-${stock.symbol}`);
            if (checkbox) checkbox.checked = true;
        });
        this.updateStockCounter();
        this.updateStartButton();
    }

    clearSelection() {
        this.selectedStocks = [];
        document.querySelectorAll('#stockList input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        this.updateStockCounter();
        this.updateStartButton();
    }

    updateStockCounter() {
        const counter = document.querySelector('.selected-count');
        if (counter) {
            counter.textContent = `Selected: ${this.selectedStocks.length} stocks`;
        }
    }

    setDateLimits() {
        const today = new Date();
        const maxDate = today.toISOString().split('T')[0];
        const minDate = new Date(today.getTime() - (365 * 24 * 60 * 60 * 1000)).toISOString().split('T')[0];

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
        const startDate = document.getElementById('startDate');
        const endDate = document.getElementById('endDate');
        
        if (startDate && endDate && startDate.value && endDate.value) {
            if (new Date(startDate.value) >= new Date(endDate.value)) {
                alert('Start date must be before end date');
                endDate.value = '';
            }
        }
        this.updateStartButton();
    }

    updateStartButton() {
        const startBtn = document.getElementById('startHammerAnalysis');
        if (!startBtn) return;

        const hasStocks = this.selectedStocks.length > 0;
        const hasTarget = document.getElementById('targetPercent')?.value;
        const hasStopLoss = document.getElementById('stopLossPercent')?.value;
        const hasValidPeriod = this.isCustomPeriod ? 
            (document.getElementById('startDate')?.value && document.getElementById('endDate')?.value) :
            this.selectedPeriod > 0;

        const isValid = hasStocks && hasTarget && hasStopLoss && hasValidPeriod;
        
        startBtn.disabled = !isValid;
        startBtn.style.opacity = isValid ? '1' : '0.6';
        startBtn.style.cursor = isValid ? 'pointer' : 'not-allowed';
    }

    async startHammerAnalysis() {
        try {
            console.log('🚀 Starting hammer analysis...');
            
            const request = {
                stocks: this.selectedStocks,
                strategy: this.selectedStrategy,
                target_percent: parseFloat(document.getElementById('targetPercent').value),
                stop_loss_percent: parseFloat(document.getElementById('stopLossPercent').value),
                start_date: this.getStartDate(),
                end_date: this.getEndDate(),
                timeframe: '15min'
            };

            console.log('📊 Analysis request:', request);

            // Show loading state
            this.showLoadingState();

            const response = await fetch('http://127.0.0.1:8000/api/backtest/hammer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const results = await response.json();
            console.log('✅ Analysis results:', results);

            // Display results
            this.displayResults(results);

        } catch (error) {
            console.error('❌ Analysis failed:', error);
            this.showError('Analysis failed: ' + error.message);
        }
    }

    // COMPLETE DISPLAY RESULTS METHOD
    async displayResults(results) {
        this.hideProgress();

        // Remove existing results section if any
        const existingResults = document.querySelector('.results-section');
        if (existingResults) {
            existingResults.remove();
        }

        // Create new results section
        const resultsSection = document.createElement('div');
        resultsSection.className = 'results-section';
        resultsSection.style.cssText = `
            margin: 20px;
            padding: 25px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            color: white;
            backdrop-filter: blur(10px);
        `;

        // Build summary cards
        const summaryCards = `
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="text-align: center; padding: 20px; border-radius: 15px; background: rgba(81, 207, 102, 0.1); border: 2px solid rgba(81, 207, 102, 0.3);">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">🎯</div>
                    <h3 style="font-size: 0.9rem; margin: 10px 0; text-transform: uppercase; color: #fff;">Target Hit</h3>
                    <div style="font-size: 2.2rem; font-weight: 800; color: #51cf66;">${results.profit_rate || 0}%</div>
                    <small style="color: #aaa; font-size: 0.8rem;">Reached +${results.target_percent || 3}% profit</small>
                </div>
                <div style="text-align: center; padding: 20px; border-radius: 15px; background: rgba(255, 212, 59, 0.1); border: 2px solid rgba(255, 212, 59, 0.3);">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">💰</div>
                    <h3 style="font-size: 0.9rem; margin: 10px 0; text-transform: uppercase; color: #fff;">Safe Profit</h3>
                    <div style="font-size: 2.2rem; font-weight: 800; color: #ffd43b;">${results.safe_rate || 0}%</div>
                    <small style="color: #aaa; font-size: 0.8rem;">Positive but below target</small>
                </div>
                <div style="text-align: center; padding: 20px; border-radius: 15px; background: rgba(255, 107, 107, 0.1); border: 2px solid rgba(255, 107, 107, 0.3);">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">🛑</div>
                    <h3 style="font-size: 0.9rem; margin: 10px 0; text-transform: uppercase; color: #fff;">Stop Loss</h3>
                    <div style="font-size: 2.2rem; font-weight: 800; color: #ff6b6b;">${results.stop_loss_rate || 0}%</div>
                    <small style="color: #aaa; font-size: 0.8rem;">Hit -${results.stop_loss_percent || 2}% stop loss</small>
                </div>
                <div style="text-align: center; padding: 20px; border-radius: 15px; background: rgba(116, 185, 255, 0.1); border: 2px solid rgba(116, 185, 255, 0.3);">
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">📊</div>
                    <h3 style="font-size: 0.9rem; margin: 10px 0; text-transform: uppercase; color: #fff;">Total Patterns</h3>
                    <div style="font-size: 2.2rem; font-weight: 800; color: #74b9ff;">${results.total_patterns || 0}</div>
                    <small style="color: #aaa; font-size: 0.8rem;">Hammer formations detected</small>
                </div>
            </div>
        `;

        // Build analysis details
        const analysisDetails = `
            <div style="background: rgba(0, 0, 0, 0.2); padding: 20px; border-radius: 15px; margin-bottom: 30px;">
                <h3 style="color: #fff; margin-bottom: 20px; font-size: 1.3rem;">📈 Analysis Details</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                        <span style="color: #ccc; font-weight: 600;">Strategy:</span>
                        <span style="color: #fff; font-weight: 700;">${results.strategy || 'Hammer Pattern'}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                        <span style="color: #ccc; font-weight: 600;">Period:</span>
                        <span style="color: #fff; font-weight: 700;">${results.period || 'Custom Range'}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                        <span style="color: #ccc; font-weight: 600;">Timeframe:</span>
                        <span style="color: #fff; font-weight: 700;">${results.timeframe || '15 Minutes'}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                        <span style="color: #ccc; font-weight: 600;">Stocks Analyzed:</span>
                        <span style="color: #fff; font-weight: 700;">${results.stocks_analyzed || this.selectedStocks.length}</span>
                    </div>
                </div>
            </div>
        `;

        // Build trades table using enhanced method
        const tradesTable = this.createTradesTable(results.detailed_trades || []);

        // Combine all sections
        resultsSection.innerHTML = `
            <h2 style="color: #ff6b6b; text-align: center; margin-bottom: 30px; font-size: 1.8rem; font-weight: 700;">
                🔨 Hammer Pattern Analysis Results
            </h2>
            ${summaryCards}
            ${analysisDetails}
            ${tradesTable}
        `;

        // Append results section
        const mainContainer = document.querySelector('.main-container');
        if (mainContainer) {
            mainContainer.parentNode.insertBefore(resultsSection, mainContainer.nextSibling);
        } else {
            document.body.appendChild(resultsSection);
        }

        // Scroll to results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }

    // FIXED: Enhanced trades table with timestamps and realistic constraints
    createTradesTable(trades) {
        if (!trades || trades.length === 0) {
            return `
                <div style="background: rgba(0, 0, 0, 0.2); padding: 20px; border-radius: 15px;">
                    <h3 style="color: #ff6b6b; margin-bottom: 20px; font-size: 1.4rem;">💼 Detailed Trades</h3>
                    <div style="text-align: center; padding: 40px; color: #888; font-style: italic; font-size: 1.1rem;">
                        No detailed trades available for this analysis period.<br>
                        <small style="font-size: 0.9rem; margin-top: 10px; display: block;">Try increasing the date range or selecting different stocks.</small>
                    </div>
                </div>
            `;
        }

        let tradesRows = '';
        trades.slice(0, 25).forEach(trade => {
            const outcomeColor = trade.outcome === 'profit' ? '#51cf66' : 
                                 trade.outcome === 'stop_loss' ? '#ff6b6b' : '#ffd43b';
            const pointsColor = (trade.points_gained || 0) >= 0 ? '#51cf66' : '#ff6b6b';
            
            // FIXED: Format times clearly and cap values
            const patternTime = trade.pattern_time || 'N/A';
            const exitTime = trade.exit_time_formatted || 'N/A';
            const minutesHeld = Math.min(trade.minutes_held || 0, 45); // Cap at 45 minutes
            const candlesHeld = Math.min(trade.candles_held || 1, 3); // Cap at 3 candles
            
            tradesRows += `
                <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.1);">
                    <td style="padding: 12px;">
                        <span style="background: rgba(255, 255, 255, 0.1); padding: 6px 12px; border-radius: 8px; font-weight: 700; color: #fff;">
                            ${trade.stock}
                        </span>
                    </td>
                    <td style="padding: 12px; color: #74b9ff; font-weight: 600; font-size: 0.85rem;">
                        ${patternTime}
                    </td>
                    <td style="padding: 12px; color: #aaa; font-weight: 500; font-size: 0.85rem;">
                        ${exitTime}
                    </td>
                    <td style="padding: 12px; font-family: 'Courier New', monospace; font-weight: 600; color: #fff;">
                        ₹${trade.entry_price || 0}
                    </td>
                    <td style="padding: 12px; font-family: 'Courier New', monospace; font-weight: 600; color: #fff;">
                        ₹${trade.exit_price || 0}
                    </td>
                    <td style="padding: 12px;">
                        <span style="background: rgba(${outcomeColor === '#51cf66' ? '81, 207, 102' : outcomeColor === '#ff6b6b' ? '255, 107, 107' : '255, 212, 59'}, 0.2); color: ${outcomeColor}; padding: 6px 12px; border-radius: 20px; font-weight: 600; font-size: 0.8rem; text-transform: uppercase;">
                            ${(trade.outcome || 'unknown').replace('_', ' ')}
                        </span>
                    </td>
                    <td style="padding: 12px; color: ${pointsColor}; font-weight: 600;">
                        ₹${trade.points_gained || 0}
                    </td>
                    <td style="padding: 12px; color: ${pointsColor}; font-weight: 600;">
                        ${(trade.percentage_gain || 0).toFixed(2)}%
                    </td>
                    <td style="padding: 12px; color: #fff; font-weight: 600;">
                        ${minutesHeld} min
                    </td>
                    <td style="padding: 12px; text-align: center;">
                        <span style="background: rgba(255, 212, 59, 0.2); color: #ffd43b; padding: 4px 8px; border-radius: 12px; font-weight: 700; font-size: 0.8rem;">
                            ${candlesHeld}
                        </span>
                    </td>
                </tr>
            `;
        });

        return `
            <div style="background: rgba(0, 0, 0, 0.2); padding: 20px; border-radius: 15px;">
                <h3 style="color: #ff6b6b; margin-bottom: 20px; font-size: 1.4rem;">
                    💼 Detailed Trades (${trades.length} trades)
                </h3>
                <div style="overflow-x: auto; max-height: 400px; overflow-y: auto; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; background: rgba(255, 255, 255, 0.02);">
                    <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem; min-width: 1000px;">
                        <thead style="background: rgba(255, 107, 107, 0.15); position: sticky; top: 0; z-index: 10;">
                            <tr>
                                <th style="padding: 15px 12px; text-align: left; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">Stock</th>
                                <th style="padding: 15px 12px; text-align: left; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">🔨 Pattern Time</th>
                                <th style="padding: 15px 12px; text-align: left; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">📤 Exit Time</th>
                                <th style="padding: 15px 12px; text-align: left; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">Entry Price</th>
                                <th style="padding: 15px 12px; text-align: left; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">Exit Price</th>
                                <th style="padding: 15px 12px; text-align: left; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">Outcome</th>
                                <th style="padding: 15px 12px; text-align: left; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">Points Gained</th>
                                <th style="padding: 15px 12px; text-align: left; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">% Gain</th>
                                <th style="padding: 15px 12px; text-align: left; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">Minutes Held</th>
                                <th style="padding: 15px 12px; text-align: center; color: #fff; font-weight: 600; border-bottom: 2px solid rgba(255, 107, 107, 0.3); font-size: 0.85rem; text-transform: uppercase;">🕯️ Candles</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${tradesRows}
                        </tbody>
                    </table>
                </div>
                ${trades.length > 25 ? `<p style="margin-top: 15px; color: #aaa; font-style: italic; text-align: center;">Showing first 25 trades of ${trades.length} total trades</p>` : ''}
                
                <div style="margin-top: 20px; padding: 15px; background: rgba(255, 255, 255, 0.05); border-radius: 10px; border-left: 4px solid #74b9ff;">
                    <h4 style="color: #74b9ff; margin-bottom: 10px;">📊 Intraday Trading Constraints:</h4>
                    <ul style="color: #ccc; font-size: 0.9rem; margin: 0; padding-left: 20px;">
                        <li>Maximum Hold Time: 45 minutes (3 candles of 15-min timeframe)</li>
                        <li>Indian Market Hours: 9:15 AM - 3:30 PM (375 minutes total)</li>
                        <li>Exit Strategy: Target/Stop-loss or forced exit after 3 candles</li>
                        <li>Pattern Detection: Hammer formations with entry at candle close</li>
                    </ul>
                </div>
            </div>
        `;
    }

    showLoadingState() {
        // Remove existing results and progress sections
        const existingResults = document.querySelector('.results-section');
        const existingProgress = document.querySelector('.progress-section');
        
        if (existingResults) existingResults.remove();
        if (existingProgress) existingProgress.remove();

        const progressSection = document.createElement('div');
        progressSection.className = 'progress-section';
        progressSection.style.cssText = `
            margin: 20px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.06);
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
            color: white;
        `;

        progressSection.innerHTML = `
            <h3 style="color: #ff6b6b; margin-bottom: 25px; font-size: 1.4rem;">🔍 Analyzing Patterns...</h3>
            <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px; justify-content: center;">
                <div style="flex: 1; max-width: 400px; height: 12px; background: rgba(255, 255, 255, 0.1); border-radius: 6px; overflow: hidden;">
                    <div class="progress-fill" style="height: 100%; background: linear-gradient(90deg, #ff6b6b, #51cf66); width: 0%; transition: width 0.8s ease; border-radius: 6px;"></div>
                </div>
                <span class="progress-percent" style="font-weight: 700; color: #ff6b6b; font-size: 1.2rem; min-width: 50px;">0%</span>
            </div>
            <div class="progress-details" style="color: #ccc; font-size: 1rem; font-style: italic;">Loading historical data...</div>
        `;

        // Append progress section
        const mainContainer = document.querySelector('.main-container');
        if (mainContainer) {
            mainContainer.parentNode.insertBefore(progressSection, mainContainer.nextSibling);
        } else {
            document.body.appendChild(progressSection);
        }

        this.animateProgress();
    }

    animateProgress() {
        const progressFill = document.querySelector('.progress-fill');
        const progressPercent = document.querySelector('.progress-percent');
        const progressDetails = document.querySelector('.progress-details');
        
        if (!progressFill) return;

        let progress = 0;
        const messages = [
            'Loading historical data...',
            'Detecting hammer patterns...',
            'Testing target and stop-loss levels...',
            'Calculating trade outcomes...',
            'Preparing results...'
        ];

        const interval = setInterval(() => {
            progress += Math.random() * 15 + 5;
            progress = Math.min(progress, 95);
            
            progressFill.style.width = progress + '%';
            progressPercent.textContent = Math.round(progress) + '%';
            
            const messageIndex = Math.floor((progress / 100) * messages.length);
            if (progressDetails && messages[messageIndex]) {
                progressDetails.textContent = messages[messageIndex];
            }
            
            if (progress >= 95) {
                clearInterval(interval);
            }
        }, 200);
    }

    hideProgress() {
        const progressSection = document.querySelector('.progress-section');
        if (progressSection) {
            progressSection.style.display = 'none';
        }
    }

    showError(message) {
        this.hideProgress();
        
        let errorSection = document.querySelector('.error-section');
        if (!errorSection) {
            errorSection = document.createElement('div');
            errorSection.className = 'error-section';
            errorSection.style.cssText = `
                margin: 20px;
                padding: 25px;
                background: rgba(255, 107, 107, 0.1);
                border: 1px solid rgba(255, 107, 107, 0.3);
                border-radius: 15px;
            `;

            const mainContainer = document.querySelector('.main-container');
            if (mainContainer) {
                mainContainer.parentNode.insertBefore(errorSection, mainContainer.nextSibling);
            } else {
                document.body.appendChild(errorSection);
            }
        }
        
        errorSection.innerHTML = `
            <div style="text-align: center;">
                <h3 style="color: #ff6b6b; margin-bottom: 15px;">❌ Analysis Error</h3>
                <p style="color: #fff; margin-bottom: 20px;">${message}</p>
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: #ff6b6b;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 20px;
                    cursor: pointer;
                    font-weight: 600;
                ">Close</button>
            </div>
        `;
    }

    getStartDate() {
        if (this.isCustomPeriod) {
            return document.getElementById('startDate').value;
        }
        
        const today = new Date();
        const daysBack = {
            1: 30,    // 1 month
            2: 90,    // 3 months  
            3: 180,   // 6 months
            4: 365    // 12 months
        };
        
        const startDate = new Date(today);
        startDate.setDate(startDate.getDate() - (daysBack[this.selectedPeriod] || 30));
        return startDate.toISOString().split('T')[0];
    }

    getEndDate() {
        if (this.isCustomPeriod) {
            return document.getElementById('endDate').value;
        }
        
        return new Date().toISOString().split('T')[0];
    }
}

// Initialize the SageForge application
const app = new SageForgeApp();
