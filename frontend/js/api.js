// API Service
class ApiService {
    constructor() {
        // Automatically detect API URL (works for both localhost and deployed)
        this.baseURL = window.location.origin + '/api';
        this.lastBacktestResults = null;
    }

    async checkHealth() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            if (!response.ok) throw new Error('Health check failed');
            return await response.json();
        } catch (error) {
            console.error('Health check error:', error);
            return { status: 'error', angel_one_connected: false };
        }
    }

    async getStocks(sector = 'all') {
        try {
            const response = await fetch(`${this.baseURL}/stocks?sector=${sector}`);
            if (!response.ok) throw new Error('Failed to fetch stocks');
            return await response.json();
        } catch (error) {
            console.error('Get stocks error:', error);
            throw error;
        }
    }

    async getSectors() {
        try {
            const response = await fetch(`${this.baseURL}/sectors`);
            if (!response.ok) throw new Error('Failed to fetch sectors');
            return await response.json();
        } catch (error) {
            console.error('Get sectors error:', error);
            return [];
        }
    }

    async getStrategies() {
        try {
            const response = await fetch(`${this.baseURL}/strategies`);
            if (!response.ok) throw new Error('Failed to fetch strategies');
            return await response.json();
        } catch (error) {
            console.error('Get strategies error:', error);
            return [];
        }
    }

    async runBacktest(params) {
        try {
            const response = await fetch(`${this.baseURL}/backtest`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Backtest failed');
            }

            this.lastBacktestResults = await response.json();
            return this.lastBacktestResults;
        } catch (error) {
            console.error('Backtest error:', error);
            throw error;
        }
    }

    async downloadPDF(params) {
        try {
            const response = await fetch(`${this.baseURL}/backtest/download-pdf`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                throw new Error('Failed to generate PDF report');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `sageforge_report_${params.strategy}_${params.start_date}_to_${params.end_date}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            return true;
        } catch (error) {
            console.error('PDF download error:', error);
            throw error;
        }
    }

    async downloadExcel(params) {
        try {
            const response = await fetch(`${this.baseURL}/backtest/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });

            if (!response.ok) {
                throw new Error('Failed to generate Excel report');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `backtest_${params.strategy}_${params.start_date}_to_${params.end_date}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            return true;
        } catch (error) {
            console.error('Excel download error:', error);
            throw error;
        }
    }

    downloadJSON(data, filename) {
        const json = JSON.stringify(data, null, 2);
        const blob = new Blob([json], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }
}

// Export as global
window.apiService = new ApiService();
