// ARGO AI Ocean Data Explorer - Frontend JavaScript
class ARGOApp {
    constructor() {
        this.apiBase = '/api';
        this.map = null;
        this.currentTab = 'dashboard';
        this.chatHistory = [];
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadSystemStats();
        await this.loadRecentData();
        this.setupMap();
        this.setupDateInputs();
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = e.currentTarget.getAttribute('data-tab');
                this.switchTab(tab);
            });
        });

        // Data generation
        document.getElementById('generate-data-btn').addEventListener('click', () => {
            this.generateSampleData();
        });

        // Map controls
        document.getElementById('refresh-map-btn').addEventListener('click', () => {
            this.loadMapData();
        });

        document.getElementById('status-filter').addEventListener('change', () => {
            this.loadMapData();
        });

        document.getElementById('institution-filter').addEventListener('change', () => {
            this.loadMapData();
        });

        // Analysis controls
        document.getElementById('analyze-btn').addEventListener('click', () => {
            this.performAnalysis();
        });

        // Depth range slider
        const depthMin = document.getElementById('depth-min');
        const depthMax = document.getElementById('depth-max');
        const depthDisplay = document.getElementById('depth-range-display');

        [depthMin, depthMax].forEach(slider => {
            slider.addEventListener('input', () => {
                const min = Math.min(depthMin.value, depthMax.value);
                const max = Math.max(depthMin.value, depthMax.value);
                depthMin.value = min;
                depthMax.value = max;
                depthDisplay.textContent = `${min} - ${max} m`;
            });
        });

        // Chat interface
        document.getElementById('send-btn').addEventListener('click', () => {
            this.sendChatMessage();
        });

        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });

        // Quick query buttons
        document.querySelectorAll('.quick-query-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const query = e.currentTarget.getAttribute('data-query');
                document.getElementById('chat-input').value = query;
                this.sendChatMessage();
            });
        });

        // Parameter comparison checkboxes
        document.querySelectorAll('.parameter-selection input[type="checkbox"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateComparisonPlot();
            });
        });
    }

    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabName).classList.add('active');

        this.currentTab = tabName;

        // Load tab-specific data
        if (tabName === 'map') {
            this.loadMapData();
        } else if (tabName === 'analysis') {
            this.loadAnalysisData();
        }
    }

    async loadSystemStats() {
        try {
            const response = await fetch(`${this.apiBase}/stats`);
            const stats = await response.json();

            document.getElementById('total-floats').textContent = stats.total_floats;
            document.getElementById('total-profiles').textContent = stats.total_profiles;
            document.getElementById('active-floats').textContent = stats.active_floats;
            document.getElementById('latest-data').textContent = stats.latest_data || 'N/A';
        } catch (error) {
            console.error('Error loading system stats:', error);
        }
    }

    async loadRecentData() {
        try {
            const response = await fetch(`${this.apiBase}/profiles?limit=50`);
            const profiles = await response.json();

            const tbody = document.getElementById('recent-data-body');
            tbody.innerHTML = '';

            profiles.forEach(profile => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${profile.profile_id}</td>
                    <td>${profile.float_id}</td>
                    <td>${new Date(profile.timestamp).toLocaleDateString()}</td>
                    <td>${profile.latitude.toFixed(2)}</td>
                    <td>${profile.longitude.toFixed(2)}</td>
                    <td>${profile.depth.toFixed(0)}</td>
                    <td>${profile.temperature ? profile.temperature.toFixed(2) : 'N/A'}</td>
                    <td>${profile.salinity ? profile.salinity.toFixed(2) : 'N/A'}</td>
                `;
                tbody.appendChild(row);
            });
        } catch (error) {
            console.error('Error loading recent data:', error);
        }
    }

    

    async generateSampleData() {
        this.showLoading();
        
        try {
            const numFloats = document.getElementById('num-floats').value;
            const daysBack = document.getElementById('days-back').value;

            const response = await fetch(`${this.apiBase}/generate-data?num_floats=${numFloats}&days_back=${daysBack}`, {
                method: 'POST'
            });

            const result = await response.json();
            
            if (response.ok) {
                alert(`Sample data generated successfully!\nFloats: ${result.floats_generated}\nProfiles: ${result.profiles_generated}`);
                await this.loadSystemStats();
                await this.loadRecentData();
            } else {
                throw new Error(result.detail || 'Failed to generate data');
            }
        } catch (error) {
            console.error('Error generating sample data:', error);
            alert('Error generating sample data: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    setupMap() {
        if (this.map) {
            this.map.remove();
        }

        this.map = L.map('map-container').setView([0, 60], 4);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);
    }

    async loadMapData() {
        try {
            const statusFilter = document.getElementById('status-filter').value;
            const institutionFilter = document.getElementById('institution-filter').value;

            let url = `${this.apiBase}/floats`;
            const params = new URLSearchParams();
            if (statusFilter) params.append('status', statusFilter);
            if (institutionFilter) params.append('institution', institutionFilter);
            if (params.toString()) url += '?' + params.toString();

            const response = await fetch(url);
            const floats = await response.json();

            // Clear existing markers
            this.map.eachLayer(layer => {
                if (layer instanceof L.Marker) {
                    this.map.removeLayer(layer);
                }
            });

            // Add new markers
            floats.forEach(float => {
                const color = float.status === 'active' ? 'green' : 'red';
                const marker = L.circleMarker([float.latitude, float.longitude], {
                    radius: 6,
                    fillColor: color,
                    color: color,
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.7
                }).addTo(this.map);

                marker.bindPopup(`
                    <strong>${float.float_id}</strong><br>
                    Status: ${float.status}<br>
                    Platform: ${float.platform_type}<br>
                    Institution: ${float.institution}<br>
                    Location: ${float.latitude.toFixed(2)}°N, ${float.longitude.toFixed(2)}°E
                `);
            });

            // Update institution filter options
            this.updateInstitutionFilter(floats);
        } catch (error) {
            console.error('Error loading map data:', error);
        }
    }

    updateInstitutionFilter(floats) {
        const institutions = [...new Set(floats.map(f => f.institution))].sort();
        const select = document.getElementById('institution-filter');
        
        // Clear existing options except "All"
        select.innerHTML = '<option value="">All</option>';
        
        institutions.forEach(institution => {
            const option = document.createElement('option');
            option.value = institution;
            option.textContent = institution;
            select.appendChild(option);
        });
    }

    setupDateInputs() {
        const today = new Date();
        const sixMonthsAgo = new Date(today.getTime() - 180 * 24 * 60 * 60 * 1000);
        
        document.getElementById('start-date').value = sixMonthsAgo.toISOString().split('T')[0];
        document.getElementById('end-date').value = today.toISOString().split('T')[0];
    }

    async loadAnalysisData() {
        // This will be called when switching to analysis tab
        // Could preload some data or set up initial state
    }

    async performAnalysis() {
        const parameter = document.getElementById('parameter-select').value;
        const depthMin = document.getElementById('depth-min').value;
        const depthMax = document.getElementById('depth-max').value;
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;

        try {
            const params = new URLSearchParams({
                min_depth: depthMin,
                max_depth: depthMax
            });
            
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);

            const response = await fetch(`${this.apiBase}/profiles?${params.toString()}`);
            const profiles = await response.json();

            this.createProfilePlot(profiles, parameter);
            this.updateComparisonPlot(profiles);
        } catch (error) {
            console.error('Error performing analysis:', error);
        }
    }

    createProfilePlot(profiles, parameter) {
        // Group profiles by profile_id
        const profileGroups = {};
        profiles.forEach(profile => {
            if (!profileGroups[profile.profile_id]) {
                profileGroups[profile.profile_id] = [];
            }
            profileGroups[profile.profile_id].push(profile);
        });

        // Create traces for each profile (limit to 10 for performance)
        const traces = [];
        const profileIds = Object.keys(profileGroups).slice(0, 10);
        
        profileIds.forEach(profileId => {
            const profileData = profileGroups[profileId].sort((a, b) => a.depth - b.depth);
            const values = profileData.map(p => p[parameter]).filter(v => v !== null);
            const depths = profileData.map(p => p.depth).filter((d, i) => profileData[i][parameter] !== null);

            if (values.length > 0) {
                traces.push({
                    x: values,
                    y: depths,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: `Profile ${profileId}`,
                    line: { width: 2 },
                    marker: { size: 4 }
                });
            }
        });

        const layout = {
            title: `${parameter.charAt(0).toUpperCase() + parameter.slice(1)} vs Depth`,
            xaxis: { title: parameter.charAt(0).toUpperCase() + parameter.slice(1) },
            yaxis: { 
                title: 'Depth (m)',
                autorange: 'reversed'
            },
            height: 400
        };

        Plotly.newPlot('profile-plot', traces, layout);
    }

    updateComparisonPlot(profiles = null) {
        if (!profiles) {
            // If no profiles provided, fetch them
            this.performAnalysis();
            return;
        }

        const selectedParams = Array.from(document.querySelectorAll('.parameter-selection input[type="checkbox"]:checked'))
            .map(cb => cb.value);

        if (selectedParams.length === 0) return;

        const traces = selectedParams.map(param => {
            const values = profiles.map(p => p[param]).filter(v => v !== null);
            return {
                x: values,
                type: 'histogram',
                name: param.charAt(0).toUpperCase() + param.slice(1),
                opacity: 0.7
            };
        });

        const layout = {
            title: 'Parameter Distributions',
            barmode: 'overlay',
            height: 400
        };

        Plotly.newPlot('comparison-plot', traces, layout);
    }

    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;

        // Add user message to chat
        this.addChatMessage(message, 'user');
        input.value = '';

        // Show loading
        this.addChatMessage('Thinking...', 'bot', true);

        try {
            const response = await fetch(`${this.apiBase}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: message })
            });

            const result = await response.json();

            // Remove loading message
            this.removeLastBotMessage();

            // Add bot response
            this.addChatMessage(result.response, 'bot');

            // Show data summary if available
            if (result.data_summary.total_records > 0) {
                this.addDataSummary(result.data_summary);
            }

        } catch (error) {
            console.error('Error sending chat message:', error);
            this.removeLastBotMessage();
            this.addChatMessage('Sorry, I encountered an error. Please try again.', 'bot');
        }
    }

    addChatMessage(content, sender, isLoading = false) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        if (isLoading) {
            messageDiv.classList.add('loading');
        }

        const icon = sender === 'user' ? 'fas fa-user' : 'fas fa-robot';
        messageDiv.innerHTML = `
            <div class="message-content">
                <i class="${icon}"></i>
                <p>${content}</p>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeLastBotMessage() {
        const messagesContainer = document.getElementById('chat-messages');
        const lastMessage = messagesContainer.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('bot-message')) {
            messagesContainer.removeChild(lastMessage);
        }
    }

    addDataSummary(summary) {
        const messagesContainer = document.getElementById('chat-messages');
        const summaryDiv = document.createElement('div');
        summaryDiv.className = 'message bot-message';
        
        let summaryText = `📊 Data Summary:\n`;
        summaryText += `• Total records: ${summary.total_records}\n`;
        summaryText += `• Parameters: ${summary.parameters_found.join(', ')}\n`;
        
        if (summary.geographic_bounds) {
            const bounds = summary.geographic_bounds;
            summaryText += `• Geographic range: ${bounds.min_lat.toFixed(2)}°N to ${bounds.max_lat.toFixed(2)}°N, `;
            summaryText += `${bounds.min_lon.toFixed(2)}°E to ${bounds.max_lon.toFixed(2)}°E`;
        }

        summaryDiv.innerHTML = `
            <div class="message-content">
                <i class="fas fa-chart-bar"></i>
                <pre style="white-space: pre-wrap; margin: 0;">${summaryText}</pre>
            </div>
        `;

        messagesContainer.appendChild(summaryDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showLoading() {
        document.getElementById('loading-overlay').classList.add('show');
    }

    hideLoading() {
        document.getElementById('loading-overlay').classList.remove('show');
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ARGOApp();
});
