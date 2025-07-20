// Configuration
const API_ENDPOINT = '/api/ferries';
const UPDATE_INTERVAL = 30000; // 30 seconds

// Application state
let map = null;
let ferries = [];
let ferryMarkers = [];
let nextSailingsData = {};
let isLoading = false;
let currentTab = 'routes';

// Initialize the app
document.addEventListener('DOMContentLoaded', function() {
    console.log('Ferry Tracker starting...');
    
    // Initialize UI immediately
    updateNextSailingsList(); // Show initial state
    
    // Fetch data
    fetchFerries();
    fetchNextSailings(); // Add initial next sailings fetch
    
    // Set up periodic updates
    setInterval(() => {
        fetchFerries();
        fetchNextSailings(); // Fetch next sailings on each interval
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

// Fetch ferry data from API (current positions)
async function fetchFerries() {
    if (isLoading) return;
    
    isLoading = true;
    
    try {
        console.log('Fetching ferry data...');
        
        // Fetch current positions (default behavior, no query params needed)
        const response = await fetch(API_ENDPOINT);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const apiResponse = await response.json();
        
        // Handle the new response format
        if (apiResponse.type === 'current-positions') {
            ferries = apiResponse.data;
        } else {
            ferries = apiResponse; // Fallback for old format
        }
        
        console.log(`Loaded information on ${ferries.length} ferries`);
        console.log('Ferry data:', ferries);
        
        updateSystemStatus();
        updateRoutesList();
        updateFerryMarkers();
        updateLastUpdated();
        
        // Hide loading states
        document.getElementById('routes-loading').classList.add('hidden');
        document.getElementById('routes-error').classList.add('hidden');
        
    } catch (error) {
        console.error('Error fetching ferries:', error);
        document.getElementById('routes-loading').classList.add('hidden');
        document.getElementById('routes-error').classList.remove('hidden');
    } finally {
        isLoading = false;
    }
}

// Fetch next sailings predictions with retry logic
async function fetchNextSailings(retryCount = 0) {
    const maxRetries = 2;
    
    try {
        console.log(`Fetching next sailings... (attempt ${retryCount + 1}/${maxRetries + 1})`);
        console.log('API endpoint:', `${API_ENDPOINT}?type=next-sailings`);
        
        // Hide error state on retry attempts
        if (retryCount === 0) {
            const errorElement = document.getElementById('next-sailings-error');
            if (errorElement) errorElement.classList.add('hidden');
        }
        
        const startTime = Date.now();
        const response = await fetch(`${API_ENDPOINT}?type=next-sailings`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache'
            }
        });
        const fetchTime = Date.now() - startTime;
        
        console.log(`Next sailings fetch took ${fetchTime}ms, status: ${response.status}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Next sailings API error response:', errorText);
            throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
        }
        
        const parseStart = Date.now();
        const apiResponse = await response.json();
        const parseTime = Date.now() - parseStart;
        
        console.log(`JSON parsing took ${parseTime}ms`);
        console.log('Next sailings data:', apiResponse);
        
        // Store the data
        nextSailingsData = apiResponse.data || {};
        console.log('Stored next sailings data keys:', Object.keys(nextSailingsData));
        
        // Update the display (this will handle loading state)
        updateNextSailingsList();
        
        console.log('Next sailings fetch completed successfully');
        
    } catch (error) {
        console.error(`Error fetching next sailings (attempt ${retryCount + 1}):`, error);
        
        // Retry logic
        if (retryCount < maxRetries) {
            console.log(`Retrying next sailings fetch in 1 second...`);
            setTimeout(() => {
                fetchNextSailings(retryCount + 1);
            }, 1000);
            return;
        }
        
        console.error('All retry attempts failed for next sailings');
        console.error('Final error details:', {
            message: error.message,
            stack: error.stack,
            name: error.name
        });
        
        // Show error state only after all retries fail
        const loadingElement = document.getElementById('next-sailings-loading');
        const errorElement = document.getElementById('next-sailings-error');
        if (loadingElement) loadingElement.classList.add('hidden');
        if (errorElement) errorElement.classList.remove('hidden');
    }
}

// Update system status overview
function updateSystemStatus() {
    const totalFerries = ferries.length;
    const activeFerries = ferries.filter(f => f.InService).length;
    
    // Calculate delayed routes
    const routeDelays = {};
    ferries.forEach(ferry => {
        const route = ferry.OpRouteAbbrev?.join(', ') || 'Unknown';
        if (!routeDelays[route]) {
            routeDelays[route] = [];
        }
        if (ferry.ScheduledDeparture && ferry.LeftDock) {
            const delayInfo = calculateDelay(ferry.ScheduledDeparture, ferry.LeftDock);
            routeDelays[route].push(delayInfo.delayMinutes);
        }
    });
    
    const delayedRoutes = Object.keys(routeDelays).filter(route => {
        const avgDelay = routeDelays[route].reduce((a, b) => a + b, 0) / routeDelays[route].length;
        return avgDelay > 0;
    }).length;
    
    // Calculate average delay
    const allDelays = Object.values(routeDelays).flat();
    const avgDelay = allDelays.length > 0 ? 
        Math.round(allDelays.reduce((a, b) => a + b, 0) / allDelays.length) : 0;
    
    document.getElementById('total-ferries').textContent = totalFerries;
    document.getElementById('active-ferries').textContent = activeFerries;
    document.getElementById('delayed-routes').textContent = delayedRoutes;
    document.getElementById('avg-delay').textContent = avgDelay > 0 ? `${avgDelay}m` : '0m';
}

// Update next sailings list
function updateNextSailingsList() {
    const container = document.getElementById('next-sailings-list');
    if (!container) return;
    
    // Always hide loading state when this function is called
    const loadingElement = document.getElementById('next-sailings-loading');
    if (loadingElement) {
        loadingElement.classList.add('hidden');
    }
    
    if (!nextSailingsData || Object.keys(nextSailingsData).length === 0) {
        // Show loading message only if we have no data at all
        if (loadingElement) {
            loadingElement.classList.remove('hidden');
        }
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    Object.entries(nextSailingsData).forEach(([routeAbbrev, routeData]) => {
        html += `
            <div class="route-section">
                <h3 class="route-title">${routeData.name} (${routeAbbrev})</h3>
                <div class="terminals-grid">
        `;
        
        Object.entries(routeData.terminals).forEach(([terminalId, terminal]) => {
            html += `
                <div class="terminal-card">
                    <h4 class="terminal-name">${terminal.terminal_name}</h4>
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

// Update routes list
function updateRoutesList() {
    const routesContainer = document.getElementById('routes-list');
    const routeGroups = groupFerriesByRoute(ferries);
    
    let html = '';
    
    Object.entries(routeGroups).forEach(([route, routeFerries]) => {
        // Calculate route status
        const routeStatus = calculateRouteStatus(routeFerries);
        
        // Create ferry items
        let ferryItems = '';
        routeFerries.forEach(ferry => {
            const delayInfo = calculateFerryDelay(ferry);
            ferryItems += `
                <li class="ferry-item">
                    <div>
                        <div class="ferry-name">${ferry.VesselName}</div>
                        <div class="ferry-route-info">${ferry.DepartingTerminalName} → ${ferry.ArrivingTerminalName || 'Unknown'}</div>
                    </div>
                    <div class="ferry-delay ${delayInfo.cssClass}">${delayInfo.displayText}</div>
                </li>
            `;
        });
        
        html += `
            <div class="route-card">
                <div class="route-header">
                    <div class="route-name">${route}</div>
                    <div class="route-status ${routeStatus.cssClass}">${routeStatus.text}</div>
                </div>
                <ul class="ferry-list">
                    ${ferryItems}
                </ul>
            </div>
        `;
    });
    
    routesContainer.innerHTML = html;
}

// Group ferries by route
function groupFerriesByRoute(ferries) {
    const groups = {};
    
    ferries.forEach(ferry => {
        const route = ferry.OpRouteAbbrev?.join(', ') || 'Unknown Route';
        if (!groups[route]) {
            groups[route] = [];
        }
        groups[route].push(ferry);
    });
    
    // Sort routes alphabetically
    const sortedGroups = {};
    Object.keys(groups).sort().forEach(key => {
        sortedGroups[key] = groups[key].sort((a, b) => a.VesselName.localeCompare(b.VesselName));
    });
    
    return sortedGroups;
}

// Calculate overall status for a route
function calculateRouteStatus(routeFerries) {
    const delays = routeFerries.map(ferry => {
        if (!ferry.ScheduledDeparture || !ferry.LeftDock) return 0;
        const delayInfo = calculateDelay(ferry.ScheduledDeparture, ferry.LeftDock);
        return delayInfo.delayMinutes;
    }).filter(delay => delay !== 0);
    
    if (delays.length === 0) {
        return { text: 'No Data', cssClass: 'status-unknown' };
    }
    
    const avgDelay = delays.reduce((a, b) => a + b, 0) / delays.length;
    
    if (avgDelay > 10) {
        return { text: 'Major Delays', cssClass: 'status-delayed' };
    } else if (avgDelay > 0) {
        return { text: 'Minor Delays', cssClass: 'status-delayed' };
    } else if (avgDelay < 0) {
        return { text: 'Running Early', cssClass: 'status-early' };
    } else {
        return { text: 'On Time', cssClass: 'status-on-time' };
    }
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
