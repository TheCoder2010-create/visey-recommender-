// Visey Recommender Test Interface JavaScript

class ViseyTestInterface {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkApiStatus();
        this.loadDataStats();
    }

    bindEvents() {
        // Status refresh
        document.getElementById('refresh-status').addEventListener('click', () => {
            this.checkApiStatus();
            this.loadDataStats();
        });

        // Recommendation form
        document.getElementById('recommendation-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.getRecommendations();
        });

        // Search form
        document.getElementById('search-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.searchContent();
        });

        // Profile form
        document.getElementById('profile-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.getUserProfile();
        });

        // WordPress management
        document.getElementById('sync-data').addEventListener('click', () => {
            this.syncWordPressData();
        });

        document.getElementById('check-wp-health').addEventListener('click', () => {
            this.checkWordPressHealth();
        });

        // Performance testing
        document.getElementById('run-load-test').addEventListener('click', () => {
            this.runLoadTest();
        });
    }

    // Utility methods
    showLoading() {
        document.getElementById('loading-overlay').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.add('hidden');
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    getToastIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    formatTime(ms) {
        if (ms < 1000) return `${ms}ms`;
        return `${(ms / 1000).toFixed(2)}s`;
    }

    formatDate(dateString) {
        if (!dateString) return 'Never';
        const date = new Date(dateString);
        return date.toLocaleString();
    }

    // API Status Check
    async checkApiStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            this.updateStatusIndicator(data.status === 'healthy');
            this.updateHealthStatus(data);
            
            // Check WordPress status
            const wpResponse = await fetch(`${this.apiBaseUrl}/wordpress/health`);
            const wpData = await wpResponse.json();
            this.updateWordPressStatus(wpData);
            
        } catch (error) {
            console.error('Status check failed:', error);
            this.updateStatusIndicator(false);
            this.showToast('Failed to check API status', 'error');
        }
    }

    updateStatusIndicator(isHealthy) {
        const statusDot = document.getElementById('api-status');
        const statusText = document.getElementById('status-text');
        
        if (isHealthy) {
            statusDot.className = 'status-dot online';
            statusText.textContent = 'Online';
        } else {
            statusDot.className = 'status-dot offline';
            statusText.textContent = 'Offline';
        }
    }

    updateHealthStatus(data) {
        document.getElementById('api-health').textContent = data.status || 'Unknown';
        document.getElementById('api-health').className = `status-value ${data.status === 'healthy' ? 'healthy' : 'unhealthy'}`;
    }

    updateWordPressStatus(data) {
        const wpStatus = data.wordpress_api?.status || 'Unknown';
        const cacheStatus = data.cache_healthy ? 'Healthy' : 'Unhealthy';
        const lastSync = this.formatDate(data.last_sync);
        
        document.getElementById('wp-status').textContent = wpStatus;
        document.getElementById('wp-status').className = `status-value ${wpStatus === 'healthy' ? 'healthy' : 'unhealthy'}`;
        
        document.getElementById('cache-status').textContent = cacheStatus;
        document.getElementById('cache-status').className = `status-value ${data.cache_healthy ? 'healthy' : 'unhealthy'}`;
        
        document.getElementById('last-sync').textContent = lastSync;
    }

    // Load Data Statistics
    async loadDataStats() {
        try {
            const dataTypes = ['posts', 'users', 'categories', 'tags'];
            
            for (const type of dataTypes) {
                const response = await fetch(`${this.apiBaseUrl}/wordpress/data/${type}`);
                const data = await response.json();
                
                document.getElementById(`${type}-count`).textContent = data.count || 0;
            }
        } catch (error) {
            console.error('Failed to load data stats:', error);
        }
    }

    // Get Recommendations
    async getRecommendations() {
        const userId = document.getElementById('user-id').value;
        const topN = document.getElementById('top-n').value;
        
        if (!userId) {
            this.showToast('Please enter a user ID', 'warning');
            return;
        }

        this.showLoading();
        const startTime = Date.now();

        try {
            const response = await fetch(`${this.apiBaseUrl}/recommend?user_id=${userId}&top_n=${topN}`);
            const data = await response.json();
            const responseTime = Date.now() - startTime;

            if (response.ok) {
                this.displayRecommendations(data, responseTime);
                this.showToast(`Got ${data.items.length} recommendations`, 'success');
            } else {
                throw new Error(data.detail || 'Failed to get recommendations');
            }
        } catch (error) {
            console.error('Recommendation error:', error);
            this.showToast(`Error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayRecommendations(data, responseTime) {
        const resultsDiv = document.getElementById('recommendation-results');
        const listDiv = document.getElementById('recommendations-list');
        
        listDiv.innerHTML = '';
        
        data.items.forEach(item => {
            const itemDiv = document.createElement('div');
            itemDiv.className = 'recommendation-item';
            itemDiv.innerHTML = `
                <div class="recommendation-header">
                    <a href="${item.link}" target="_blank" class="recommendation-title">
                        ${item.title}
                    </a>
                    <span class="recommendation-score">${item.score}</span>
                </div>
                <div class="recommendation-reason">${item.reason}</div>
            `;
            listDiv.appendChild(itemDiv);
        });
        
        document.getElementById('results-count').textContent = `${data.items.length} recommendations`;
        document.getElementById('response-time').textContent = `Response time: ${this.formatTime(responseTime)}`;
        
        resultsDiv.classList.remove('hidden');
    }

    // Search Content
    async searchContent() {
        const query = document.getElementById('search-query').value;
        
        if (!query.trim()) {
            this.showToast('Please enter a search query', 'warning');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`${this.apiBaseUrl}/wordpress/search?q=${encodeURIComponent(query)}&limit=10`);
            const data = await response.json();

            if (response.ok) {
                this.displaySearchResults(data);
                this.showToast(`Found ${data.count} results`, 'success');
            } else {
                throw new Error(data.detail || 'Search failed');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showToast(`Search error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displaySearchResults(data) {
        const resultsDiv = document.getElementById('search-results');
        
        resultsDiv.innerHTML = `
            <h4>Search Results (${data.count})</h4>
            ${data.results.map(item => `
                <div class="search-item">
                    <div class="search-title">${item.title}</div>
                    <div class="search-excerpt">${item.excerpt || 'No excerpt available'}</div>
                    <small><a href="${item.link}" target="_blank">View Post</a></small>
                </div>
            `).join('')}
        `;
        
        resultsDiv.classList.remove('hidden');
    }

    // Get User Profile
    async getUserProfile() {
        const userId = document.getElementById('profile-user-id').value;
        
        if (!userId) {
            this.showToast('Please enter a user ID', 'warning');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`${this.apiBaseUrl}/wordpress/users/${userId}`);
            const data = await response.json();

            if (response.ok) {
                this.displayUserProfile(data);
                this.showToast('Profile loaded successfully', 'success');
            } else {
                throw new Error(data.detail || 'Failed to load profile');
            }
        } catch (error) {
            console.error('Profile error:', error);
            this.showToast(`Profile error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayUserProfile(data) {
        const resultsDiv = document.getElementById('profile-results');
        
        resultsDiv.innerHTML = `
            <h4>User Profile</h4>
            <div class="profile-info">
                <div class="profile-field">
                    <div class="profile-field-label">Name</div>
                    <div class="profile-field-value">${data.name || 'N/A'}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Email</div>
                    <div class="profile-field-value">${data.email || 'N/A'}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Industry</div>
                    <div class="profile-field-value">${data.industry || 'N/A'}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Stage</div>
                    <div class="profile-field-value">${data.stage || 'N/A'}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Team Size</div>
                    <div class="profile-field-value">${data.team_size || 'N/A'}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Funding</div>
                    <div class="profile-field-value">${data.funding || 'N/A'}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Location</div>
                    <div class="profile-field-value">${data.location || 'N/A'}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Registered</div>
                    <div class="profile-field-value">${this.formatDate(data.registered_date)}</div>
                </div>
            </div>
        `;
        
        resultsDiv.classList.remove('hidden');
    }

    // Sync WordPress Data
    async syncWordPressData() {
        this.showLoading();

        try {
            const response = await fetch(`${this.apiBaseUrl}/wordpress/sync`, {
                method: 'POST'
            });
            const data = await response.json();

            if (response.ok) {
                this.displaySyncResults(data);
                this.showToast('WordPress data synced successfully', 'success');
                this.loadDataStats(); // Refresh stats
            } else {
                throw new Error(data.detail || 'Sync failed');
            }
        } catch (error) {
            console.error('Sync error:', error);
            this.showToast(`Sync error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displaySyncResults(data) {
        const resultsDiv = document.getElementById('sync-results');
        
        resultsDiv.innerHTML = `
            <h4>Sync Results</h4>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Users Synced</div>
                    <div class="stat-value">${data.users_synced}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Posts Synced</div>
                    <div class="stat-value">${data.posts_synced}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Categories</div>
                    <div class="stat-value">${data.categories_synced}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Tags</div>
                    <div class="stat-value">${data.tags_synced}</div>
                </div>
            </div>
            <p><strong>Duration:</strong> ${this.formatTime(data.duration * 1000)}</p>
            ${data.errors.length > 0 ? `
                <div style="margin-top: 15px;">
                    <strong>Errors:</strong>
                    <ul>
                        ${data.errors.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        `;
        
        resultsDiv.classList.remove('hidden');
    }

    // Check WordPress Health
    async checkWordPressHealth() {
        this.showLoading();

        try {
            const response = await fetch(`${this.apiBaseUrl}/wordpress/health`);
            const data = await response.json();

            this.displayWordPressHealth(data);
            this.showToast('WordPress health check completed', 'success');
        } catch (error) {
            console.error('WordPress health check error:', error);
            this.showToast(`Health check error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    displayWordPressHealth(data) {
        const resultsDiv = document.getElementById('wp-health-results');
        
        resultsDiv.innerHTML = `
            <h4>WordPress Health Status</h4>
            <div class="profile-info">
                <div class="profile-field">
                    <div class="profile-field-label">API Status</div>
                    <div class="profile-field-value ${data.wordpress_api?.status === 'healthy' ? 'text-success' : 'text-error'}">
                        ${data.wordpress_api?.status || 'Unknown'}
                    </div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Auth Status</div>
                    <div class="profile-field-value">${data.wordpress_api?.auth_status || 'Unknown'}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Cache Status</div>
                    <div class="profile-field-value ${data.cache_healthy ? 'text-success' : 'text-error'}">
                        ${data.cache_healthy ? 'Healthy' : 'Unhealthy'}
                    </div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Service Status</div>
                    <div class="profile-field-value">${data.service_status || 'Unknown'}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Last Sync</div>
                    <div class="profile-field-value">${this.formatDate(data.last_sync)}</div>
                </div>
                <div class="profile-field">
                    <div class="profile-field-label">Sync Status</div>
                    <div class="profile-field-value">${data.sync_status || 'Unknown'}</div>
                </div>
            </div>
        `;
        
        resultsDiv.classList.remove('hidden');
    }

    // Run Load Test
    async runLoadTest() {
        const requestCount = parseInt(document.getElementById('load-test-requests').value);
        
        this.showLoading();
        
        const resultsDiv = document.getElementById('performance-results');
        resultsDiv.classList.remove('hidden');
        
        const results = [];
        const startTime = Date.now();
        
        try {
            // Run requests in parallel
            const promises = Array.from({length: requestCount}, async (_, i) => {
                const requestStart = Date.now();
                try {
                    const response = await fetch(`${this.apiBaseUrl}/recommend?user_id=1&top_n=5`);
                    const requestEnd = Date.now();
                    return {
                        success: response.ok,
                        responseTime: requestEnd - requestStart,
                        status: response.status
                    };
                } catch (error) {
                    return {
                        success: false,
                        responseTime: Date.now() - requestStart,
                        error: error.message
                    };
                }
            });
            
            const responses = await Promise.all(promises);
            const totalTime = Date.now() - startTime;
            
            // Calculate metrics
            const successfulRequests = responses.filter(r => r.success).length;
            const successRate = (successfulRequests / requestCount) * 100;
            const avgResponseTime = responses.reduce((sum, r) => sum + r.responseTime, 0) / requestCount;
            const requestsPerSecond = (requestCount / totalTime) * 1000;
            
            // Update metrics display
            document.getElementById('avg-response-time').textContent = this.formatTime(avgResponseTime);
            document.getElementById('success-rate').textContent = `${successRate.toFixed(1)}%`;
            document.getElementById('requests-per-second').textContent = requestsPerSecond.toFixed(2);
            
            // Create performance chart
            this.createPerformanceChart(responses);
            
            this.showToast(`Load test completed: ${successRate.toFixed(1)}% success rate`, 
                          successRate > 95 ? 'success' : successRate > 80 ? 'warning' : 'error');
            
        } catch (error) {
            console.error('Load test error:', error);
            this.showToast(`Load test error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    createPerformanceChart(responses) {
        const canvas = document.getElementById('performance-chart');
        const ctx = canvas.getContext('2d');
        
        // Clear previous chart
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Prepare data
        const responseTimes = responses.map(r => r.responseTime);
        const labels = responses.map((_, i) => i + 1);
        
        // Simple chart implementation
        const maxTime = Math.max(...responseTimes);
        const minTime = Math.min(...responseTimes);
        const range = maxTime - minTime;
        
        const chartWidth = canvas.width - 60;
        const chartHeight = canvas.height - 60;
        const barWidth = chartWidth / responses.length;
        
        // Draw axes
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        
        // Y-axis
        ctx.beginPath();
        ctx.moveTo(40, 20);
        ctx.lineTo(40, chartHeight + 20);
        ctx.stroke();
        
        // X-axis
        ctx.beginPath();
        ctx.moveTo(40, chartHeight + 20);
        ctx.lineTo(chartWidth + 40, chartHeight + 20);
        ctx.stroke();
        
        // Draw bars
        ctx.fillStyle = '#2563eb';
        responses.forEach((response, i) => {
            const barHeight = range > 0 ? ((response.responseTime - minTime) / range) * chartHeight : chartHeight / 2;
            const x = 40 + (i * barWidth);
            const y = chartHeight + 20 - barHeight;
            
            ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        });
        
        // Labels
        ctx.fillStyle = '#64748b';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        
        // Y-axis labels
        ctx.textAlign = 'right';
        ctx.fillText(`${maxTime}ms`, 35, 25);
        ctx.fillText(`${minTime}ms`, 35, chartHeight + 25);
        
        // Title
        ctx.textAlign = 'center';
        ctx.font = '14px sans-serif';
        ctx.fillStyle = '#1e293b';
        ctx.fillText('Response Times', chartWidth / 2 + 40, 15);
    }
}

// Initialize the interface when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ViseyTestInterface();
});