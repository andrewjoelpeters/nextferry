// Configuration
const API_ENDPOINT = '/api/ferries';
const UPDATE_INTERVAL = 30000; // 30 seconds
const DISPLAYED_ROUTES = ['sea-bi', 'ed-king'];
const TERMINAL_ORDER = {
    'sea-bi': ['3', '7'], // Bainbridge (3) before Seattle (7)
    'ed-king': ['12', '8']  // Kingston (12) before Edmonds (8)
};

// Application state
let map = null;
let ferries = [];
let ferryMarkers = [];
let nextSailingsData = {};
let isLoading = false;
let currentTab = 'next-sailings'; // Default to next-sailings tab

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    console.log('Ferry Tracker starting...');
    
    // Initialize UI and fetch data
    updateNextSailingsList();
    fetchCombinedData();
    
    // Set up periodic updates
    setInterval(() => {
        fetchCombinedData();
    }, UPDATE_INTERVAL);
});

// Tab switching functionality
function showTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`button[onclick="showTab('${tabName}')"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');

    currentTab = tabName;

    // Initialize map if switching to map tab
    if (tabName === 'map' && !map) {
        initializeMap();
    }
}

// Initialize the Leaflet map
function initializeMap() {
    map = L.map('map').setView([47.6062, -122.3321], 10);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    addMapLegend();
    updateFerryMarkers();
    
    console.log('Map initialized');
}

// Create a ferry marker
function createFerryMarker(ferry) {
    let markerColor = '#666';
    
    if (!ferry.InService) {
        markerColor = '#dc3545';
    } else if (ferry.AtDock) {
        markerColor = '#28a745';
    } else {
        markerColor = '#ffc107';
    }
    
    const markerIcon = L.divIcon({
        html: `
            <div style="
                width: 0;
                height: 0;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-bottom: 16px solid ${markerColor};
                transform: rotate(${ferry.Heading}deg);
                transform-origin: center bottom;
                filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
            "></div>
        `,
        className: 'ferry-marker',
        iconSize: [16, 16],
        iconAnchor: [8, 14]
    });
    
    const marker = L.marker([ferry.Latitude, ferry.Longitude], {
        icon: markerIcon,
        title: ferry.VesselName
    });
    
    marker.on('click', function() {
        showFerryDetails(ferry);
    });
    
    return marker;
}

// Update ferry markers on the map
function updateFerryMarkers() {
    if (!map) return;
    
    ferryMarkers.forEach(marker => map.removeLayer(marker));
    ferryMarkers = [];
    
    ferries.forEach(ferry => {
        if (ferry.InService && ferry.Latitude && ferry.Longitude) {
            const marker = createFerryMarker(ferry);
            marker.addTo(map);
            ferryMarkers.push(marker);
        }
    });
    
    console.log(`Updated ${ferryMarkers.length} ferry markers`);
}

// Show ferry details in the side panel
function showFerryDetails(ferry) {
    let status = 'Unknown';
    let statusClass = 'status-unknown';

    if (!ferry.InService) {
        status = 'Out of Service';
        statusClass = 'status-delayed';
    } else if (ferry.AtDock) {
        status = 'At Dock';
        statusClass = 'status-on-time';
    } else {
        status = 'In Transit';
        statusClass = 'status-early';
    }

    const formatTime = (date) => date ? parseMicrosoftJsonDateToTime(date) : 'N/A';

    let delayText = 'N/A';
    if (ferry.ScheduledDeparture) {
        // If ferry has departed, calculate current delay
        if (ferry.LeftDock) {
            const delayMeta = calculateDelay(ferry.ScheduledDeparture, ferry.LeftDock);
            delayText = delayMeta.delayText;
        }
        // If ferry hasn't departed, use cached delay from server
        else if (ferry.cachedDelay) {
            delayText = ferry.cachedDelay;
        }
    }

    document.getElementById('ferry-details').innerHTML = `
        <h3>${ferry.VesselName}</h3>
        <div class="route-status ${statusClass}">${status}</div>
        <p><strong>From:</strong> ${ferry.DepartingTerminalName}</p>
        <p><strong>To:</strong> ${ferry.ArrivingTerminalName || 'Unknown'}</p>
        <p><strong>Scheduled:</strong> ${formatTime(ferry.ScheduledDeparture)}</p>
        <p><strong>Departed:</strong> ${formatTime(ferry.LeftDock)}</p>
        <p><strong>Delay:</strong> ${delayText}</p>
        <p><strong>ETA:</strong> ${formatTime(ferry.Eta)}</p>
        <p><strong>Speed:</strong> ${ferry.Speed.toFixed(1)} knots</p>
        <p><strong>Route:</strong> ${ferry.OpRouteAbbrev?.join(', ') || 'Unknown'}</p>
    `;

    document.getElementById('ferry-info-panel').classList.remove('hidden');
}

// Close ferry details panel
document.addEventListener('click', function(e) {
    if (e.target.id === 'close-panel') {
        document.getElementById('ferry-info-panel').classList.add('hidden');
    }
});

// Fetch combined ferry data (positions + next sailings) from API
async function fetchCombinedData(retryCount = 0) {
    if (isLoading) return;
    
    const maxRetries = 2;
    isLoading = true;
    
    try {
        console.log('Fetching combined ferry data...');
        
        // Hide error states on first attempt
        if (retryCount === 0) {
            const nextSailingsError = document.getElementById('next-sailings-error');
            if (nextSailingsError) nextSailingsError.classList.add('hidden');
        }
        
        // Single API call for both vessel positions and next sailings
        const response = await fetch(API_ENDPOINT, {
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log(data)
        
        if (data && data.type === 'combined') {
            // Update vessel positions
            if (data.vessels) {
                ferries = data.vessels;
                updateFerryMarkers();
                updateLastUpdated();
            }
            
            // Update next sailings
            if (data.nextSailings) {
                nextSailingsData = data.nextSailings;
                console.log(`Loaded next sailings for ${Object.keys(nextSailingsData).length} routes`);
                updateNextSailingsList();
            }
        }
        
        // Hide loading states
        const nextSailingsLoading = document.getElementById('next-sailings-loading');
        if (nextSailingsLoading) nextSailingsLoading.classList.add('hidden');
        
    } catch (error) {
        console.error('Error fetching combined data:', error);
        
        // Retry logic
        if (retryCount < maxRetries) {
            console.log(`Retrying... (${retryCount + 1}/${maxRetries})`);
            setTimeout(() => fetchCombinedData(retryCount + 1), 1000);
            return;
        }
        
        // Show error states after all retries fail
        const nextSailingsLoading = document.getElementById('next-sailings-loading');
        const nextSailingsError = document.getElementById('next-sailings-error');
        if (nextSailingsLoading) nextSailingsLoading.classList.add('hidden');
        if (nextSailingsError) nextSailingsError.classList.remove('hidden');
    } finally {
        isLoading = false;
    }
}

// Legacy function - kept for compatibility but no longer used
async function fetchNextSailings(retryCount = 0) {
    const maxRetries = 2;
    
    try {
        // Hide error state on first attempt
        if (retryCount === 0) {
            const errorElement = document.getElementById('next-sailings-error');
            if (errorElement) errorElement.classList.add('hidden');
        }
        
        const response = await fetch(`${API_ENDPOINT}?type=next-sailings`, {
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const apiResponse = await response.json();
        nextSailingsData = apiResponse.data || {};
        updateNextSailingsList();
        
    } catch (error) {
        console.error(`Error fetching next sailings (attempt ${retryCount + 1}):`, error);
        
        // Retry logic
        if (retryCount < maxRetries) {
            setTimeout(() => fetchNextSailings(retryCount + 1), 1000);
            return;
        }
        
        // Show error state after all retries fail
        const loadingElement = document.getElementById('next-sailings-loading');
        const errorElement = document.getElementById('next-sailings-error');
        if (loadingElement) loadingElement.classList.add('hidden');
        if (errorElement) errorElement.classList.remove('hidden');
    }
}



// Update next sailings list
function updateNextSailingsList() {
    const container = document.getElementById('next-sailings-list');
    const loadingElement = document.getElementById('next-sailings-loading');
    if (!container) return;
    
    // Show loading if no data, otherwise hide loading
    if (!nextSailingsData || Object.keys(nextSailingsData).length === 0) {
        if (loadingElement) loadingElement.classList.remove('hidden');
        container.innerHTML = '';
        return;
    }
    
    if (loadingElement) loadingElement.classList.add('hidden');
    
    let html = '';
    
    // Routes are now filtered server-side, so display all returned routes
    Object.entries(nextSailingsData).forEach(([routeAbbrev, routeData]) => {
        html += `
            <div class="route-section">
                <h3 class="route-title">${routeData.name})</h3>
                <div class="terminals-grid">
        `;
        
        // Order terminals according to TERMINAL_ORDER (west to east)
        const terminalOrder = TERMINAL_ORDER[routeAbbrev] || Object.keys(routeData.terminals);
        const orderedTerminals = terminalOrder
            .map(terminalId => [terminalId, routeData.terminals[terminalId]])
            .filter(([terminalId, terminal]) => terminal); // Only include terminals that exist
        
        orderedTerminals.forEach(([terminalId, terminal]) => {
            html += `
                <div class="terminal-card">
                    <h4 class="terminal-name">Leaving  ${terminal.terminal_name}</h4>
                    <div class="sailings-list">
            `;
            
            if (terminal.sailings && terminal.sailings.length > 0) {
                terminal.sailings.slice(0, 3).forEach((sailing, index) => {
                    const currentTime = new Date();
                    const scheduledTime = parseTimeString(sailing.scheduled_departure);
                    const estimatedTime = parseTimeString(sailing.estimated_departure);
                    
                    let timeUntil = 'N/A';
                    let statusClass = 'status-unknown';
                    let delayText = '';
                    
                    if (estimatedTime) {
                        const minutesUntil = Math.round((estimatedTime - currentTime) / (1000 * 60));
                        if (minutesUntil <= 2 && minutesUntil >= -5) {
                            timeUntil = 'Now';
                            statusClass = 'status-departing';
                        } else if (minutesUntil > 2) {
                            if (minutesUntil < 60) {
                                timeUntil = `${minutesUntil}m`;
                            } else {
                                const hours = Math.floor(minutesUntil / 60);
                                const mins = minutesUntil % 60;
                                timeUntil = `${hours}h ${mins}m`;
                            }
                        } else {
                            timeUntil = 'Departed';
                            statusClass = 'status-departed';
                        }
                    }
                    
                    if (sailing.estimated_delay > 0) {
                        delayText = ` (+${Math.round(sailing.estimated_delay)}m)`;
                        statusClass = 'status-delayed';
                    } else if (sailing.estimated_delay < 0) {
                        delayText = ` (${Math.round(sailing.estimated_delay)}m)`;
                        statusClass = 'status-early';
                    } else {
                        statusClass = 'status-on-time';
                    }
                    
                    html += `
                        <div class="sailing-item ${statusClass}">
                            <div class="time-until-prominent">${timeUntil}</div>
                            <div class="departure-times">
                                <div class="scheduled-time">Scheduled: ${sailing.scheduled_departure}</div>
                                ${sailing.estimated_departure !== sailing.scheduled_departure ? 
                                    `<div class="estimated-time">Estimated: ${sailing.estimated_departure}${delayText}</div>` : 
                                    delayText ? `<div class="delay-only">${delayText.trim()}</div>` : ''}
                            </div>
                            ${sailing.vessel_name ? `<div class="vessel-name">${sailing.vessel_name}</div>` : ''}
                        </div>
                    `;
                });
            } else {
                html += '<div class="no-sailings">No upcoming sailings</div>';
            }
            
            html += `
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Helper function to parse time strings
function parseTimeString(timeStr) {
    if (!timeStr) return null;
    
    const now = new Date();
    const [time, period] = timeStr.split(' ');
    const [hours, minutes] = time.split(':').map(Number);
    
    let hour24 = hours;
    if (period === 'PM' && hours !== 12) {
        hour24 += 12;
    } else if (period === 'AM' && hours === 12) {
        hour24 = 0;
    }
    
    const result = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hour24, minutes);
    
    // If the time is more than 12 hours in the past, assume it's for tomorrow
    // This prevents showing departures as 24 hours away when they're actually soon
    const timeDiff = result - now;
    if (timeDiff < -12 * 60 * 60 * 1000) {
        result.setDate(result.getDate() + 1);
    }
    
    return result;
}



// Calculate delay information for display
function calculateFerryDelay(ferry) {
    if (!ferry.ScheduledDeparture) {
        return {
            displayText: 'No data',
            cssClass: 'status-unknown'
        };
    }
    
    let delayText = 'No data';
    let cssClass = 'status-unknown';
    
    // If ferry has departed, calculate current delay
    if (ferry.LeftDock) {
        const delayData = calculateDelay(ferry.ScheduledDeparture, ferry.LeftDock);
        if (!delayData.error) {
            delayText = delayData.delayText;
            cssClass = delayData.status === 'on-time' ? 'status-on-time' :
                      delayData.status === 'early' ? 'status-early' : 'status-delayed';
        }
    }
    // If ferry hasn't departed, use cached delay from server
    else if (ferry.cachedDelay) {
        delayText = ferry.cachedDelay;
        // Determine CSS class from cached delay text
        if (delayText.includes('late')) {
            cssClass = 'status-delayed';
        } else if (delayText.includes('early')) {
            cssClass = 'status-early';
        } else if (delayText.includes('on time')) {
            cssClass = 'status-on-time';
        }
    }
    
    return {
        displayText: delayText,
        cssClass: cssClass
    };
}

// Add map legend
function addMapLegend() {
    const legend = L.control({ position: 'bottomleft' });
    
    legend.onAdd = function(map) {
        const div = L.DomUtil.create('div', 'map-legend');
        div.innerHTML = `
            <h4>Ferry Status</h4>
            <div><span class="legend-color" style="background: #28a745;"></span> At Dock</div>
            <div><span class="legend-color" style="background: #ffc107;"></span> In Transit</div>
            <div><span class="legend-color" style="background: #dc3545;"></span> Out of Service</div>
        `;
        return div;
    };
    
    legend.addTo(map);
}

// Update last updated timestamp
function updateLastUpdated() {
    const now = new Date();
    document.getElementById('last-updated').textContent = now.toLocaleTimeString();
}

// Utility functions (keeping your existing ones)
function parseMicrosoftJsonDateToTime(msDateString) {
    const match = /\/Date\((\d+)([+-]\d{4})\)\//.exec(msDateString);
    if (!match) return null;

    const millis = parseInt(match[1], 10);
    const date = new Date(millis);

    return date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

function calculateDelay(expectedTimeString, actualTimeString) {
    const expectedMatch = /\/Date\((\d+)([+-]\d{4})\)\//.exec(expectedTimeString);
    const actualMatch = /\/Date\((\d+)([+-]\d{4})\)\//.exec(actualTimeString);
    
    if (!expectedMatch || !actualMatch) {
        return { error: "Invalid timestamp format" };
    }
    
    const expectedMillis = parseInt(expectedMatch[1], 10);
    const actualMillis = parseInt(actualMatch[1], 10);
    
    const expectedDate = new Date(expectedMillis);
    const actualDate = new Date(actualMillis);
    
    const diffMillis = actualDate.getTime() - expectedDate.getTime();
    const diffMinutes = Math.round(diffMillis / (1000 * 60));
    
    const expectedTime = expectedDate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    const actualTime = actualDate.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    
    let status, delayText;
    if (diffMinutes > 0) {
        status = "delayed";
        delayText = `${diffMinutes} min late`;
    } else if (diffMinutes < 0) {
        status = "early";
        delayText = `${Math.abs(diffMinutes)} min early`;
    } else {
        status = "on-time";
        delayText = "on time";
    }
    
    return {
        expectedTime,
        actualTime,
        delayMinutes: diffMinutes,
        status,
        delayText
    };
}
