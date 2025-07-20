import { cacheDelay, getCachedDelay } from './kv-helpers.js';

// Simple utility functions
function parseFerryTime(msDateString) {
    if (!msDateString) return null;
    const match = msDateString.match(/\/Date\((\d+)/);
    return match ? new Date(parseInt(match[1])) : null;
}

function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
}

function calculateDelay(expectedTimeString, actualTimeString) {
    const expectedMatch = /\/Date\((\d+)/.exec(expectedTimeString);
    const actualMatch = /\/Date\((\d+)/.exec(actualTimeString);
    
    if (!expectedMatch || !actualMatch) {
        return { error: "Invalid timestamp format" };
    }
    
    const expectedDate = new Date(parseInt(expectedMatch[1]));
    const actualDate = new Date(parseInt(actualMatch[1]));
    
    const diffMinutes = Math.round((actualDate - expectedDate) / (1000 * 60));
    
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
    
    return { delayMinutes: diffMinutes, status, delayText };
}

// Simplified ferry API calls
async function fetchWithRetry(url, retries = 2) {
    for (let i = 0; i <= retries; i++) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            if (i === retries) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000)); // 1s delay
        }
    }
}

async function getCurrentVessels(apiKey) {
    const url = `https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations?apiaccesscode=${apiKey}`;
    const data = await fetchWithRetry(url);
    return data.filter(ferry => ferry.InService && ferry.OpRouteAbbrev?.length > 0);
}

async function getRouteSchedule(apiKey, routeId) {
    const url = `https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/${routeId}/false?apiaccesscode=${apiKey}`;
    return await fetchWithRetry(url);
}

async function getRoutes(apiKey) {
    const url = `https://www.wsdot.wa.gov/ferries/api/schedule/rest/schedroutes?apiaccesscode=${apiKey}`;
    const data = await fetchWithRetry(url);
    
    // Return simple mapping
    const mapping = {};
    data.forEach(route => {
        mapping[route.RouteAbbrev] = {
            id: route.RouteID,
            name: route.Description
        };
    });
    return mapping;
}

// Simplified prediction logic
async function predictNextSailings(apiKey, routeAbbrev = null) {
    try {
        const [vessels, routes] = await Promise.all([
            getCurrentVessels(apiKey),
            getRoutes(apiKey)
        ]);
        
        const routesToCheck = routeAbbrev ? [routeAbbrev] : Object.keys(routes);
        const predictions = {};
        
        for (const route of routesToCheck) {
            if (!routes[route]) continue;
            
            try {
                const routeId = routes[route].id;
                const schedule = await getRouteSchedule(apiKey, routeId);
                const routePredictions = await predictRouteNext(vessels, schedule, route);
                
                if (Object.keys(routePredictions).length > 0) {
                    predictions[route] = {
                        name: routes[route].name,
                        terminals: routePredictions
                    };
                }
            } catch (error) {
                console.warn(`Skipping route ${route}:`, error.message);
            }
        }
        
        return predictions;
    } catch (error) {
        console.error('Error predicting sailings:', error);
        throw error;
    }
}

async function predictRouteNext(vessels, schedule, routeAbbrev) {
    const predictions = {};
    const now = new Date();
    
    // Find vessels on this route with their current status
    const routeVessels = vessels.filter(v => 
        v.OpRouteAbbrev?.includes(routeAbbrev)
    );
    
    if (routeVessels.length === 0) return predictions;
    
    // Create vessel information map with current status and sailing assignment
    const vesselInfo = new Map();
    
    routeVessels.forEach(vessel => {
        const vesselPos = vessel.VesselPositionNum;
        if (!vesselPos || !vessel.ScheduledDeparture) return;
        
        let currentDelay = 0;
        
        // Calculate current delay
        if (vessel.LeftDock) {
            // Vessel has departed - calculate actual delay
            const delayInfo = calculateDelay(vessel.ScheduledDeparture, vessel.LeftDock);
            if (!delayInfo.error) {
                currentDelay = delayInfo.delayMinutes;
            }
        } else if (vessel.cachedDelay) {
            // Vessel hasn't departed but has cached delay info
            const match = vessel.cachedDelay.match(/(\d+)\s*min\s*(late|early)/);
            if (match) {
                currentDelay = match[2] === 'late' ? parseInt(match[1]) : -parseInt(match[1]);
            }
        }
        
        const scheduledTime = parseFerryTime(vessel.ScheduledDeparture);
        const hasLeftDock = vessel.LeftDock !== null;
        
        vesselInfo.set(vesselPos, {
            name: vessel.VesselName,
            currentDelay: currentDelay,
            scheduledDeparture: scheduledTime,
            hasLeftDock: hasLeftDock,
            departingTerminalId: vessel.DepartingTerminalID,
            atDock: vessel.AtDock
        });
    });
    
    // Process each terminal combination
    for (const combo of schedule.TerminalCombos || []) {
        const terminalId = combo.DepartingTerminalID;
        const terminalName = combo.DepartingTerminalName;
        
        // Get upcoming sailings for this terminal, sorted by time
        const upcomingSailings = combo.Times
            ?.filter(time => {
                const departTime = parseFerryTime(time.DepartingTime);
                return departTime && departTime > now;
            })
            .sort((a, b) => {
                const timeA = parseFerryTime(a.DepartingTime);
                const timeB = parseFerryTime(b.DepartingTime);
                return timeA - timeB;
            })
            .slice(0, 4);
        
        if (!upcomingSailings?.length) continue;
        
        const sailingPredictions = [];
        
        // Track running delays for each vessel position
        const vesselDelayTracker = new Map();
        
        for (let i = 0; i < Math.min(upcomingSailings.length, 3); i++) {
            const sailing = upcomingSailings[i];
            const vesselPosition = sailing.VesselPositionNum;
            const scheduledTime = parseFerryTime(sailing.DepartingTime);
            
            if (!scheduledTime || !vesselPosition) continue;
            
            const vessel = vesselInfo.get(vesselPosition);
            let estimatedDelay = 0;
            let vesselName = null;
            
            if (vessel) {
                vesselName = vessel.name;
                
                // Check if this sailing matches the vessel's current scheduled departure
                const timeDiff = Math.abs(scheduledTime.getTime() - vessel.scheduledDeparture.getTime());
                
                if (!vessel.hasLeftDock && timeDiff < 60000) {
                    // Vessel is waiting at dock for this exact sailing
                    estimatedDelay = vessel.currentDelay;
                    vesselDelayTracker.set(vesselPosition, estimatedDelay);
                } else if (vessel.hasLeftDock) {
                    // Vessel has left dock - this sailing is its next return trip
                    // Apply delay propagation based on turnaround time
                    
                    // Find previous sailing for this vessel (the one it just departed for)
                    const previousSailingTime = vessel.scheduledDeparture;
                    const turnaroundTime = calculateTurnaroundTimeFromTimes(previousSailingTime, scheduledTime);
                    
                    if (turnaroundTime < 25) {
                        // Very tight turnaround - most delay carries over
                        estimatedDelay = Math.max(0, vessel.currentDelay * .95);
                    } else if (turnaroundTime < 45) {
                        // Normal turnaround - some recovery possible
                        estimatedDelay = Math.max(0, vessel.currentDelay * .9);
                    } else {
                        // Long turnaround - significant recovery possible
                        estimatedDelay = Math.max(0, vessel.currentDelay * .8);
                    }
                    
                    vesselDelayTracker.set(vesselPosition, estimatedDelay);
                } else {
                    // Use tracked delay from previous iterations
                    estimatedDelay = vesselDelayTracker.get(vesselPosition) || 0;
                }
            } else {
                // No vessel info - assume on time
                estimatedDelay = 0;
            }
            
            // Handle blocking delays from previous sailings
            if (i > 0) {
                const previousSailing = sailingPredictions[i - 1];
                if (previousSailing && previousSailing.estimated_delay > 10) {
                    const prevScheduledTime = parseFerryTime(upcomingSailings[i-1].DepartingTime);
                    const prevEstimatedDepartTime = new Date(prevScheduledTime.getTime() + (previousSailing.estimated_delay * 60000));
                    
                    // If previous sailing will depart after this one is scheduled
                    if (prevEstimatedDepartTime > scheduledTime) {
                        const blockingDelayMinutes = Math.round((prevEstimatedDepartTime.getTime() - scheduledTime.getTime()) / (60000));
                        // Add buffer for vessel change operations
                        estimatedDelay = Math.max(estimatedDelay, blockingDelayMinutes + 5);
                    }
                }
            }
            
            const estimatedTime = new Date(scheduledTime.getTime() + (estimatedDelay * 60000));
            
            sailingPredictions.push({
                scheduled_departure: formatTime(scheduledTime),
                estimated_departure: formatTime(estimatedTime),
                estimated_delay: estimatedDelay,
                vessel_position: vesselPosition,
                vessel_name: vesselName
            });
        }
        
        if (sailingPredictions.length > 0) {
            predictions[terminalId] = {
                terminal_name: terminalName,
                sailings: sailingPredictions
            };
        }
    }
    
    return predictions;
}

// Helper function to calculate turnaround time between two departure times
function calculateTurnaroundTimeFromTimes(previousDepartureTime, nextDepartureTime) {
    if (!previousDepartureTime || !nextDepartureTime) return 30; // Default
    
    // Estimate crossing time (could be made route-specific)
    const crossingTime = 35; // minutes
    const arrivalTime = new Date(previousDepartureTime.getTime() + (crossingTime * 60000));
    
    // Calculate turnaround: time between arrival and next departure
    const turnaroundMs = nextDepartureTime.getTime() - arrivalTime.getTime();
    return Math.max(10, Math.round(turnaroundMs / (60 * 1000))); // Minimum 10 minutes
}

// Main handler
export default async function handler(req, res) {
    try {
        // CORS headers
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

        const apiKey = process.env.WSDOT_API_KEY;
        if (!apiKey) {
            return res.status(500).json({ error: 'API key missing' });
        }

        const { route, type } = req.query;
        
        // Next sailings prediction
        if (type === 'next-sailings') {
            const predictions = await predictNextSailings(apiKey, route);
            return res.status(200).json({
                type: 'next-sailings',
                data: predictions,
                timestamp: new Date().toISOString()
            });
        }
        
        // Current positions (existing functionality)
        const ferries = await getCurrentVessels(apiKey);
        
        const processedFerries = await Promise.allSettled(
            ferries.map(async (ferry) => {
                const tripId = `${ferry.OpRouteAbbrev?.join(',')}-${ferry.VesselPositionNum}`;
                
                try {
                    // Cache delay if ferry has departed
                    if (ferry.ScheduledDeparture && ferry.LeftDock) {
                        const delayInfo = calculateDelay(ferry.ScheduledDeparture, ferry.LeftDock);
                        if (!delayInfo.error) {
                            await cacheDelay(tripId, delayInfo.delayText);
                            ferry.cachedDelay = delayInfo.delayText;
                        }
                    }
                    // Get cached delay if available
                    else if (ferry.ScheduledDeparture) {
                        const cachedDelay = await getCachedDelay(tripId);
                        if (cachedDelay) {
                            ferry.cachedDelay = cachedDelay;
                        }
                    }
                } catch (error) {
                    console.warn(`Error processing ferry ${ferry.VesselName}:`, error);
                }
                
                return ferry;
            })
        );
        
        // Extract successful results
        const results = processedFerries
            .filter(result => result.status === 'fulfilled')
            .map(result => result.value);
        
        res.status(200).json({
            type: 'current-positions',
            data: results,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('API Error:', error);
        res.status(500).json({ 
            error: 'Service temporarily unavailable',
            timestamp: new Date().toISOString()
        });
    }
}
