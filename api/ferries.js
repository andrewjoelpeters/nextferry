import { kv } from '@vercel/kv';
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

// Create a timeout wrapper for fetch requests
function fetchWithTimeout(url, options = {}, timeoutMs = 10000) {
    return Promise.race([
        fetch(url, options),
        new Promise((_, reject) => 
            setTimeout(() => reject(new Error(`Request timeout after ${timeoutMs}ms`)), timeoutMs)
        )
    ]);
}

// Simplified ferry API calls with timeout and retry
async function fetchWithRetry(url, retries = 2, timeoutMs = 10000) {
    for (let i = 0; i <= retries; i++) {
        try {
            const response = await fetchWithTimeout(url, {}, timeoutMs);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn(`API call attempt ${i + 1}/${retries + 1} failed:`, error.message);
            if (i === retries) throw error;
            await new Promise(resolve => setTimeout(resolve, 1000)); // 1s delay
        }
    }
}

async function getCurrentVessels(apiKey) {
    const start = Date.now();
    const url = `https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations?apiaccesscode=${apiKey}`;
    console.log('🚢 Fetching vessel locations from WSDOT API...');
    const data = await fetchWithRetry(url);
    const filtered = data.filter(ferry => ferry.InService && ferry.OpRouteAbbrev?.length > 0);
    const time = Date.now() - start;
    console.log(`  ✅ Vessel locations: ${time}ms (${data.length} total, ${filtered.length} in service)`);
    return filtered;
}

async function getRouteSchedule(apiKey, routeId) {
    const start = Date.now();
    const url = `https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/${routeId}/false?apiaccesscode=${apiKey}`;
    console.log(`    📅 Fetching schedule for route ID ${routeId}...`);
    const result = await fetchWithRetry(url);
    const time = Date.now() - start;
    console.log(`    ✅ Schedule fetched: ${time}ms`);
    return result;
}

async function getRoutes(apiKey) {
    const start = Date.now();
    const url = `https://www.wsdot.wa.gov/ferries/api/schedule/rest/schedroutes?apiaccesscode=${apiKey}`;
    console.log('🗺️  Fetching routes from WSDOT API...');
    const data = await fetchWithRetry(url);
    
    // Return simple mapping
    const mapping = {};
    data.forEach(route => {
        mapping[route.RouteAbbrev] = {
            id: route.RouteID,
            name: route.Description
        };
    });
    const time = Date.now() - start;
    console.log(`  ✅ Routes fetched: ${time}ms (${data.length} routes)`);
    return mapping;
}

// KV cache keys
const CACHE_FLUSH_DATE_KEY = 'ferry:cache_flush_date';
const SCHEDULE_CACHE_PREFIX = 'ferry:schedule:';

// Cache schedule data in KV store
async function cacheSchedule(routeId, cacheFlushDate, scheduleData) {
    try {
        const cacheKey = `${SCHEDULE_CACHE_PREFIX}${routeId}-${cacheFlushDate}`;
        // Cache for 24 hours (86400 seconds) - schedules don't change often
        await kv.set(cacheKey, scheduleData, { ex: 86400 });
        console.log(`💾 Cached schedule for route ${routeId}`);
    } catch (error) {
        console.warn('Error caching schedule:', error.message);
    }
}

// Get cached schedule data from KV store
async function getCachedSchedule(routeId, cacheFlushDate) {
    try {
        const cacheKey = `${SCHEDULE_CACHE_PREFIX}${routeId}-${cacheFlushDate}`;
        const cachedData = await kv.get(cacheKey);
        return cachedData;
    } catch (error) {
        console.warn('Error getting cached schedule:', error.message);
        return null;
    }
}

// Cache the flush date in KV store
async function cacheFlushDate(flushDate) {
    try {
        await kv.set(CACHE_FLUSH_DATE_KEY, flushDate, { ex: 3600 }); // Cache for 1 hour
    } catch (error) {
        console.warn('Error caching flush date:', error.message);
    }
}

// Get cached flush date from KV store
async function getCachedFlushDate() {
    try {
        return await kv.get(CACHE_FLUSH_DATE_KEY);
    } catch (error) {
        console.warn('Error getting cached flush date:', error.message);
        return null;
    }
}

// Parse .NET JSON date format like /Date(1753069201237-0700)/
function parseDotNetDate(dateString) {
    if (typeof dateString !== 'string') return dateString;
    const match = dateString.match(/\/Date\((\d+)([+-]\d{4})?\)\//); 
    if (match) {
        const timestamp = parseInt(match[1]);
        return new Date(timestamp).toISOString();
    }
    return dateString;
}

// Unified vessel processing - fetches vessels and processes delays consistently
async function getVesselsWithDelays(apiKey) {
    console.log('📡 Fetching vessel positions and processing delays...');
    const start = Date.now();
    
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
    
    const time = Date.now() - start;
    console.log(`✅ Vessel positions: ${time}ms (${results.length} total, ${results.filter(f => f.InService).length} in service)`);
    
    return results;
}

// Check if WSDOT schedule data has been updated
async function checkCacheFlushDate(apiKey) {
    try {
        const url = `https://www.wsdot.wa.gov/ferries/api/schedule/rest/cacheflushdate?apiaccesscode=${apiKey}`;
        const response = await fetchWithTimeout(url, {
            headers: {
                'Accept': 'application/json'
            }
        }, 5000); // 5 second timeout for cache flush date
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        const rawDate = typeof data === 'string' ? data : String(data);
        const cacheFlushDate = parseDotNetDate(rawDate);
        console.log(`🕒 Cache flush date from WSDOT: ${rawDate} -> ${cacheFlushDate}`);
        return cacheFlushDate;
    } catch (error) {
        console.warn('Could not fetch cache flush date:', error.message);
        return null;
    }
}


async function predictNextSailings(apiKey, vessels, routeAbbrev = null) {
    // Add overall timeout to prevent Vercel function timeout
    const PREDICTION_TIMEOUT = 25000; // 25 seconds, leaving 5s buffer for Vercel's 30s limit
    
    return Promise.race([
        predictNextSailingsInternal(apiKey, vessels, routeAbbrev),
        new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Prediction timeout - operation took too long')), PREDICTION_TIMEOUT)
        )
    ]);
}

// Internal prediction logic
async function predictNextSailingsInternal(apiKey, vessels, routeAbbrev = null) {
    try {
        console.log('🚢 Starting predictNextSailings...');
        const overallStart = Date.now();
        
        // Check if schedule data needs to be refreshed using KV store
        const [currentCacheFlushDate, lastCachedFlushDate] = await Promise.all([
            checkCacheFlushDate(apiKey),
            getCachedFlushDate()
        ]);
        
        console.log(`🔍 Cache comparison (KV store):`);
        console.log(`  Last cached flush date: ${lastCachedFlushDate}`);
        console.log(`  Current cache flush date: ${currentCacheFlushDate}`);
        
        const shouldRefreshCache = !lastCachedFlushDate || 
            currentCacheFlushDate !== lastCachedFlushDate;
        
        console.log(`  Should refresh cache: ${shouldRefreshCache}`);
        console.log(`    - No cached date: ${!lastCachedFlushDate}`);
        console.log(`    - Dates different: ${currentCacheFlushDate !== lastCachedFlushDate}`);
        
        if (shouldRefreshCache && currentCacheFlushDate) {
            console.log('📅 Schedule cache needs refresh - updating KV store');
            await cacheFlushDate(currentCacheFlushDate);
        } else {
            console.log('✅ Using cached schedule data from KV store');
        }
        
        console.log('🗺️  Fetching routes...');
        const routes = await getRoutes(apiKey);
        
        console.log(`✅ Using ${vessels.length} vessels (passed from handler), Routes: ${Object.keys(routes).length}`);
        
        const routesToCheck = routeAbbrev ? [routeAbbrev] : Object.keys(routes);
        console.log(`🔍 Processing ${routesToCheck.length} routes: ${routesToCheck.join(', ')}`);
        
        // Parallel schedule fetching with KV store caching and aggressive timeout
        const scheduleStart = Date.now();
        const SCHEDULE_FETCH_TIMEOUT = 15000; // 15 seconds total for all schedule fetches
        
        const schedulePromises = routesToCheck
            .filter(route => routes[route]) // Only valid routes
            .map(async (route) => {
                const routeId = routes[route].id;
                
                // Check KV cache first
                const cachedSchedule = await getCachedSchedule(routeId, currentCacheFlushDate);
                if (cachedSchedule) {
                    return { route, schedule: cachedSchedule, fromCache: true };
                }
                
                try {
                    // Use shorter timeout for individual schedule fetches (6 seconds)
                    const schedule = await fetchWithRetry(
                        `https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/${routeId}/true?apiaccesscode=${apiKey}`,
                        1, // Only 1 retry to save time
                        6000 // 6 second timeout per attempt
                    );
                    // Cache the result in KV store (fire and forget)
                    cacheSchedule(routeId, currentCacheFlushDate, schedule);
                    return { route, schedule, fromCache: false };
                } catch (error) {
                    console.warn(`Failed to fetch schedule for ${route}:`, error.message);
                    return { route, schedule: null, error: error.message };
                }
            });
        
        // Add timeout to the entire parallel schedule fetching operation
        let scheduleResults;
        try {
            scheduleResults = await Promise.race([
                Promise.all(schedulePromises),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Schedule fetching timeout')), SCHEDULE_FETCH_TIMEOUT)
                )
            ]);
        } catch (error) {
            console.warn('Schedule fetching timed out, proceeding with partial data:', error.message);
            // Return partial results - only the ones that completed successfully
            const settledPromises = await Promise.allSettled(schedulePromises);
            scheduleResults = settledPromises.map(result => 
                result.status === 'fulfilled' ? result.value : { route: 'unknown', schedule: null, error: 'timeout' }
            );
        }
        const scheduleTime = Date.now() - scheduleStart;
        
        const cachedCount = scheduleResults.filter(r => r.fromCache).length;
        const fetchedCount = scheduleResults.filter(r => !r.fromCache && r.schedule).length;
        const failedCount = scheduleResults.filter(r => r.error).length;
        
        console.log(`📊 Schedules: ${cachedCount} cached, ${fetchedCount} fetched, ${failedCount} failed in ${scheduleTime}ms`);
        
        // Process predictions in parallel too
        const predictionStart = Date.now();
        const predictionPromises = scheduleResults
            .filter(result => result.schedule) // Only successful schedule fetches
            .map(async ({ route, schedule }) => {
                try {
                    const routePredictions = await predictRouteNext(vessels, schedule, route);
                    return {
                        route,
                        predictions: routePredictions,
                        terminalCount: Object.keys(routePredictions).length
                    };
                } catch (error) {
                    console.warn(`Prediction failed for ${route}:`, error.message);
                    return { route, predictions: {}, terminalCount: 0 };
                }
            });
        
        const predictionResults = await Promise.all(predictionPromises);
        const predictionTime = Date.now() - predictionStart;
        
        // Build final predictions object
        const predictions = {};
        predictionResults.forEach(({ route, predictions: routePredictions, terminalCount }) => {
            if (terminalCount > 0) {
                predictions[route] = {
                    name: routes[route].name,
                    terminals: routePredictions
                };
            }
        });
        
        const overallTime = Date.now() - overallStart;
        console.log(`\n📊 PERFORMANCE SUMMARY:`);
        console.log(`  Total time: ${overallTime}ms (was ~54s, now ~${Math.round(overallTime/1000)}s)`);
        console.log(`  Schedule fetching: ${scheduleTime}ms (parallel)`);
        console.log(`  Prediction calculations: ${predictionTime}ms (parallel)`);
        console.log(`  Cache efficiency: ${cachedCount}/${scheduleResults.length} cached`);
        console.log(`  Success rate: ${Object.keys(predictions).length}/${routesToCheck.length} routes`);
        
        return predictions;
    } catch (error) {
        console.error('❌ Error predicting sailings:', error);
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
    console.log(`\n🏢 Processing ${schedule.TerminalCombos?.length || 0} terminals for route ${routeAbbrev}...`);
    for (const combo of schedule.TerminalCombos || []) {
        const terminalId = combo.DepartingTerminalID;
        const terminalName = combo.DepartingTerminalName;
        
        console.log(`\n📍 Terminal: ${terminalName} (ID: ${terminalId})`);
        console.log(`   Available sailings: ${combo.Times?.length || 0}`);
        
        // Get upcoming sailings for this terminal, sorted by time
        const upcomingSailings = combo.Times
            ?.filter(time => {
                const departTime = parseFerryTime(time.DepartingTime);
                const isUpcoming = departTime && departTime > now;
                if (departTime) {
                    console.log(`   ${departTime.toLocaleTimeString()} - ${isUpcoming ? 'UPCOMING' : 'PAST'} (Vessel ${time.VesselPositionNum})`);
                }
                return isUpcoming;
            })
            .sort((a, b) => {
                const timeA = parseFerryTime(a.DepartingTime);
                const timeB = parseFerryTime(b.DepartingTime);
                return timeA - timeB;
            })
            .slice(0, 4);
        
        console.log(`   ✅ Found ${upcomingSailings?.length || 0} upcoming sailings`);
        
        if (!upcomingSailings?.length) {
            console.log(`   ⚠️ No upcoming sailings for ${terminalName}`);
            continue;
        }
        
        const sailingPredictions = [];
        
        // Track running delays for each vessel position
        const vesselDelayTracker = new Map();
        
        // CRITICAL: First, check if any ferry is currently at the dock for this terminal
        // A ferry at the dock MUST be the next departure, regardless of schedule timing
        let ferryAtDock = null;
        for (const [vesselPos, vesselData] of vesselInfo) {
            if (vesselData.atDock && vesselData.departingTerminalId === terminalId && !vesselData.hasLeftDock) {
                ferryAtDock = { vesselPos, vesselData };
                console.log(`   ⚓ Ferry at dock: ${vesselData.name} (ready to depart)`);
                break;
            }
        }
        
        if (!ferryAtDock) {
            console.log(`   🚢 No ferry currently at dock for ${terminalName}`);
        }
        
        console.log(`\n   🕰️ Processing ${Math.min(upcomingSailings.length, 3)} upcoming sailings:`);
        
        for (let i = 0; i < Math.min(upcomingSailings.length, 3); i++) {
            const sailing = upcomingSailings[i];
            const vesselPosition = sailing.VesselPositionNum;
            const scheduledTime = parseFerryTime(sailing.DepartingTime);
            
            console.log(`\n   Sailing ${i + 1}: ${scheduledTime.toLocaleTimeString()} (Vessel Position ${vesselPosition})`);
            
            if (!scheduledTime || !vesselPosition) {
                console.log(`     ❌ Invalid sailing data - skipping`);
                continue;
            }
            
            const vessel = vesselInfo.get(vesselPosition);
            let estimatedDelay = 0;
            let vesselName = null;
            
            if (vessel) {
                vesselName = vessel.name;
                console.log(`     🚢 Assigned vessel: ${vesselName}`);
                console.log(`     📍 Vessel status: ${vessel.atDock ? 'At dock' : 'In transit'}`);
                console.log(`     ⏰ Vessel scheduled departure: ${vessel.scheduledDeparture.toLocaleTimeString()}`);
                
                // PRIORITY LOGIC: If this is the first sailing and there's a ferry at dock,
                // that ferry MUST be assigned to this sailing, regardless of vessel position matching
                if (i === 0 && ferryAtDock && ferryAtDock.vesselData.departingTerminalId === terminalId) {
                    // Override vessel assignment - the ferry at dock gets priority
                    vesselName = ferryAtDock.vesselData.name;
                    estimatedDelay = ferryAtDock.vesselData.currentDelay;
                    vesselDelayTracker.set(ferryAtDock.vesselPos, estimatedDelay);
                    console.log(`     ❗ OVERRIDE: Ferry at dock ${vesselName} takes priority (${estimatedDelay}min delay)`);
                } else {
                    // Normal logic for subsequent sailings or when no ferry at dock
                    const timeDiff = Math.abs(scheduledTime.getTime() - vessel.scheduledDeparture.getTime());
                    console.log(`     🔄 Scheduled turnaround time (${vessel.scheduledDeparture.toLocaleTimeString()} → ${scheduledTime.toLocaleTimeString()}): ${Math.round(timeDiff / 60000)}min`);
                    
                    if (!vessel.hasLeftDock && timeDiff < 60000) {
                        // Vessel is waiting at dock for this exact sailing
                        estimatedDelay = vessel.currentDelay;
                        console.log(`     ⚓ Vessel waiting at dock - using current delay: ${estimatedDelay}min`);
                    } else {
                        // Calculate delay based on vessel's current status and turnaround time
                        const baseDelay = vessel.currentDelay;
                        const turnaroundTime = calculateTurnaroundTimeFromTimes(
                            vessel.scheduledDeparture, 
                            scheduledTime
                        );
                        
                        console.log(`     🔄 Base delay: ${baseDelay}min, Turnaround time: ${turnaroundTime}min`);
                        
                        // Apply cascading delay logic
                        const previousDelay = vesselDelayTracker.get(vesselPosition) || 0;
                        estimatedDelay = Math.max(baseDelay, previousDelay) + Math.max(0, baseDelay - turnaroundTime);
                        
                        console.log(`     🔗 Previous delay: ${previousDelay}min, Calculated delay: ${estimatedDelay}min`);
                    }
                    
                    vesselDelayTracker.set(vesselPosition, estimatedDelay);
                }
            } else {
                console.log(`     ⚠️ No vessel info found for position ${vesselPosition}`);
                vesselName = `Position ${vesselPosition}`;
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

// Configuration - routes to display (can be overridden by query param)
const DEFAULT_DISPLAYED_ROUTES = ['sea-bi', 'ed-king'];

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

        const { route, routes } = req.query;
        
        // Determine which routes to process
        let routesToProcess;
        if (route) {
            // Single route specified
            routesToProcess = [route];
        } else if (routes) {
            // Multiple routes specified (comma-separated)
            routesToProcess = routes.split(',').map(r => r.trim());
        } else {
            // Use default routes
            routesToProcess = DEFAULT_DISPLAYED_ROUTES;
        }
        
        console.log(`🎯 Processing routes: ${routesToProcess.join(', ')}`);
        
        // Fetch vessels with delay processing once for all request types
        const vessels = await getVesselsWithDelays(apiKey);
        
        // Process predictions for filtered routes only
        const predictions = {};
        for (const routeAbbrev of routesToProcess) {
            const routePredictions = await predictNextSailings(apiKey, vessels, routeAbbrev);
            if (routePredictions && Object.keys(routePredictions).length > 0) {
                Object.assign(predictions, routePredictions);
            }
        }
        
        res.status(200).json({
            type: 'combined',
            vessels: vessels,
            nextSailings: predictions,
            routesProcessed: routesToProcess,
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
