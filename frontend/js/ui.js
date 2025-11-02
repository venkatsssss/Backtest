// UI Handler
class UIHandler {
    constructor() {
        this.elements = {
            apiStatus: document.getElementById('apiStatus'),
            stockList: document.getElementById('stockList'),
            selectedCount: document.getElementById('selectedCount'),
            progressSection: document.getElementById('progressSection'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),
            resultsSection: document.getElementById('resultsSection'),
            resultsSummary: document.getElementById('resultsSummary'),
            resultsTableBody: document.getElementById('resultsTableBody')
        };
    }

    updateStatus(status, connected) {
        const statusDot = this.elements.apiStatus.querySelector('.status-dot');
        const statusText = this.elements.apiStatus.querySelector('.status-text');

        statusDot.className = 'status-dot';
        
        if (connected) {
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
        } else if (status === 'error') {
            statusDot.classList.add('error');
            statusText.textContent = 'Connection Error';
        } else {
            statusText.textContent = 'Limited Mode';
        }
    }

    renderStocks(stocks, selectedStocks) {
        if (!stocks || stocks.length === 0) {
            this.elements.stockList.innerHTML = '<div class="loading">No stocks found</div>';
            return;
        }

        this.elements.stockList.innerHTML = stocks.map(stock => `
            <label class="stock-item">
                <input 
                    type="checkbox" 
                    value="${stock.symbol}"
                    ${selectedStocks.includes(stock.symbol) ? 'checked' : ''}
                    onchange="app.toggleStock('${stock.symbol}')"
                >
                <div class="stock-info">
                    <div class="stock-symbol">${stock.symbol}</div>
                    <div class="stock-name">${stock.name}</div>
                </div>
            </label>
        `).join('');
    }

    updateSelectedCount(count) {
        this.elements.selectedCount.textContent = `${count} stock${count !== 1 ? 's' : ''} selected`;
    }

    showProgress() {
        this.elements.progressSection.style.display = 'block';
        this.elements.resultsSection.style.display = 'none';
        this.animateProgress();
    }

    animateProgress() {
        let progress = 0;
        const messages = [
            'Connecting to Angel One API...',
            'Fetching historical data...',
            'Detecting hammer patterns...',
            'Simulating trades...',
            'Calculating results...',
            'Preparing report...'
        ];

        const interval = setInterval(() => {
            progress += Math.random() * 15 + 5;
            progress = Math.min(progress, 95);

            this.elements.progressFill.style.width = progress + '%';
            
            const messageIndex = Math.floor((progress / 100) * messages.length);
            if (messages[messageIndex]) {
                this.elements.progressText.textContent = messages[messageIndex];
            }

            if (progress >= 95) {
                clearInterval(interval);
            }
        }, 300);

        this.progressInterval = interval;
    }

    hideProgress() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        this.elements.progressFill.style.width = '100%';
        this.elements.progressText.textContent = 'Complete!';
        
        setTimeout(() => {
            this.elements.progressSection.style.display = 'none';
        }, 500);
    }

    displayResults(results) {
        this.hideProgress();
        this.elements.resultsSection.style.display = 'block';

        // Render summary cards
        this.renderSummary(results);

        // Render trades table
        this.renderTradesTable(results.trades);

        // Scroll to results
        setTimeout(() => {
            this.elements.resultsSection.scrollIntoView({ behavior: 'smooth' });
        }, 100);
    }

    renderSummary(results) {
        const summaryHTML = `
            <div class="metric-card success">
                <div class="metric-icon">🎯</div>
                <div class="metric-label">Target Hit Rate</div>
                <div class="metric-value">${results.target_hit_rate}%</div>
                <div class="metric-desc">${results.target_hit_count} trades</div>
            </div>

            <div class="metric-card danger">
                <div class="metric-icon">🛑</div>
                <div class="metric-label">Stop Loss Rate</div>
                <div class="metric-value">${results.stop_loss_rate}%</div>
                <div class="metric-desc">${results.stop_loss_count} trades</div>
            </div>

            <div class="metric-card warning">
                <div class="metric-icon">📊</div>
                <div class="metric-label">End of Day Exits</div>
                <div class="metric-value">${results.eod_exit_count}</div>
                <div class="metric-desc">No target/SL hit</div>
            </div>

            <div class="metric-card info">
                <div class="metric-icon">💰</div>
                <div class="metric-label">Total Patterns</div>
                <div class="metric-value">${results.total_patterns}</div>
                <div class="metric-desc">Avg Return: ${results.avg_return}%</div>
            </div>
        `;

        this.elements.resultsSummary.innerHTML = summaryHTML;
    }

    renderTradesTable(trades) {
        if (!trades || trades.length === 0) {
            this.elements.resultsTableBody.innerHTML = `
                <tr>
                    <td colspan="16" style="text-align: center; padding: 40px;">
                        No trades found for the selected criteria
                    </td>
                </tr>
            `;
            return;
        }

        const tradesHTML = trades.map(trade => {
            const outcomeClass = this.getOutcomeClass(trade.outcome);
            const returnColor = trade.percentage_return >= 0 ? '#51cf66' : '#ff6b6b';
            const maxProfitColor = trade.max_profit_points > 0 ? '#51cf66' : '#888';

            return `
                <tr>
                    <td><strong>${trade.stock}</strong></td>
                    <td>${trade.pattern_date}</td>
                    <td>${trade.pattern_time}</td>
                    <td>₹${trade.entry_price}</td>
                    <td>₹${trade.target_price}</td>
                    <td>₹${trade.stop_loss_price}</td>
                    <td>₹${trade.exit_price}</td>
                    <td>${trade.exit_time}</td>
                    <td>${trade.exit_reason}</td>
                    <td style="color: ${maxProfitColor}; font-weight: 600;">
                        ₹${trade.max_profit_points}
                    </td>
                    <td style="color: ${maxProfitColor}; font-weight: 600;">
                        ${trade.max_profit_percent}%
                    </td>
                    <td style="color: ${returnColor}">₹${trade.points_gained}</td>
                    <td style="color: ${returnColor}; font-weight: 600;">${trade.percentage_return}%</td>
                    <td>${trade.minutes_held} min</td>
                    <td>${trade.candles_held}</td>
                    <td>
                        <span class="outcome-badge ${outcomeClass}">
                            ${this.formatOutcome(trade.outcome)}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');

        this.elements.resultsTableBody.innerHTML = tradesHTML;
    }

    getOutcomeClass(outcome) {
        const classMap = {
            'target_hit': 'target',
            'stop_loss': 'stoploss',
            'eod_exit': 'eod'
        };
        return classMap[outcome] || 'eod';
    }

    formatOutcome(outcome) {
        const formatMap = {
            'target_hit': 'Target',
            'stop_loss': 'Stop Loss',
            'eod_exit': 'EOD Exit'
        };
        return formatMap[outcome] || outcome;
    }

    showError(message) {
        this.hideProgress();
        
        alert(`Error: ${message}\n\nPlease check your inputs and try again.`);
    }

    showLoading(element) {
        if (element) {
            element.innerHTML = '<div class="loading">Loading...</div>';
        }
    }
}

// Export as global
window.uiHandler = new UIHandler();