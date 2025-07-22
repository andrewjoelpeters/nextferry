// Import fetchers, cache helpers, utilities from wsdot-api
import {
    checkCacheFlushDate,
    getRoutes,
    getRouteSchedule,
    getCachedFlushDate,
    cacheFlushDateInKV,
    getCachedSchedule,
    cacheSchedule,
    parseFerryTime,
    calculateDelay,
    formatTime
} from './wsdot-api.js';

// -------------------- Public Prediction Function --------------------

export async function predictNextSailings(apiKey, vessels, routeAbbrev = null) {
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
            await cacheFlushDateInKV(currentCacheFlushDate);
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
                    const schedule = await getRouteSchedule(apiKey, routeId)
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

// -------------------- Supporting Helpers --------------------

export async function predictRouteNext(vessels, schedule, routeAbbrev) {
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
        
        // Get all sailings for this terminal, sorted by time
        const allSailings = combo.Times
            ?.map(time => ({
                ...time,
                departTime: parseFerryTime(time.DepartingTime)
            }))
            .filter(time => time.departTime) // Only valid times
            .sort((a, b) => a.departTime - b.departTime);
            
        if (!allSailings?.length) {
            console.log(`   ⚠️ No valid sailings for ${terminalName}`);
            continue;
        }
        
        // Log all sailings for debugging
        allSailings.forEach(time => {
            const isUpcoming = time.departTime > now;
            console.log(`   ${time.departTime.toLocaleTimeString()} - ${isUpcoming ? 'UPCOMING' : 'PAST'} (Vessel ${time.VesselPositionNum})`);
        });
        
        // Find the current sailing based on ferry positions, not time
        let currentSailingIndex = -1;
        let currentFerry = null;
        
        // Priority 1: Ferry at dock for this terminal
        const ferryAtDock = Array.from(vesselInfo.values())
            .find(vessel => vessel.atDock && vessel.departingTerminalId === terminalId && !vessel.hasLeftDock);
            
        if (ferryAtDock) {
            currentFerry = ferryAtDock;
            console.log(`   ⚓ Ferry at dock: ${ferryAtDock.name} - this is the current sailing`);
        } else {
            // Priority 2: Ferry en route to this terminal (find the closest one by ETA)
            const ferriesEnRoute = Array.from(vesselInfo.values())
                .filter(vessel => vessel.arrivingTerminalId === terminalId && !vessel.atDock)
                .sort((a, b) => {
                    // Sort by ETA (closest first)
                    const etaA = a.eta || new Date(Date.now() + 60 * 60000); // Default 1 hour if no ETA
                    const etaB = b.eta || new Date(Date.now() + 60 * 60000);
                    return etaA - etaB;
                });
                
            if (ferriesEnRoute.length > 0) {
                currentFerry = ferriesEnRoute[0];
                console.log(`   🚢 Ferry en route: ${currentFerry.name} (ETA: ${currentFerry.eta?.toLocaleTimeString() || 'unknown'}) - this is the current sailing`);
            }
        }
        
        if (currentFerry) {
            // Find the sailing that matches this ferry's scheduled departure
            currentSailingIndex = allSailings.findIndex(sailing => {
                const timeDiff = Math.abs(sailing.departTime.getTime() - currentFerry.scheduledDeparture.getTime());
                return timeDiff < 60000; // Within 1 minute
            });
            
            if (currentSailingIndex >= 0) {
                console.log(`   🎯 Found current ferry's scheduled sailing at index ${currentSailingIndex}`);
            } else {
                console.log(`   ⚠️ Current ferry's scheduled time doesn't match any sailing - using first sailing`);
                currentSailingIndex = 0;
            }
        } else {
            console.log(`   ⚠️ No ferry at dock or en route - using first sailing`);
            currentSailingIndex = 0;
        }
        
        if (currentSailingIndex < 0 || currentSailingIndex >= allSailings.length) {
            console.log(`   ⚠️ Invalid sailing index`);
            continue;
        }
        
        // Get the current sailing and the next few sailings
        const upcomingSailings = allSailings.slice(currentSailingIndex, currentSailingIndex + 4);
        
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
        let ferryAtDockData = null;
        for (const [vesselPos, vesselData] of vesselInfo) {
            if (vesselData.atDock && vesselData.departingTerminalId === terminalId && !vesselData.hasLeftDock) {
                ferryAtDockData = { vesselPos, vesselData };
                console.log(`   ⚓ Ferry at dock: ${vesselData.name} (ready to depart)`);
                break;
            }
        }
        
        if (!ferryAtDockData) {
            console.log(`   🚢 No ferry currently at dock for ${terminalName}`);
        }
        
        // If there's a ferry at dock, it IS the immediate next sailing
        if (ferryAtDockData) {
            const ferryScheduledTime = ferryAtDockData.vesselData.scheduledDeparture;
            const currentTime = new Date();
            
            console.log(`   🚨 Ferry at dock scheduled departure: ${ferryScheduledTime.toLocaleTimeString()}`);
            
            // Use cached delay as baseline, but update if ferry has been waiting longer
            const cachedDelay = ferryAtDockData.vesselData.currentDelay;
            const timeSinceScheduled = (currentTime.getTime() - ferryScheduledTime.getTime()) / (60 * 1000);
            const actualDelay = Math.max(0, timeSinceScheduled);
            
            // Use the greater of cached delay or actual time since scheduled
            const estimatedDelay = Math.max(cachedDelay, actualDelay);
            const estimatedTime = new Date(currentTime.getTime());
            
            console.log(`   🕰️ Cached delay: ${cachedDelay}min, Time since scheduled: ${Math.round(actualDelay)}min`);
            console.log(`   📊 Using estimated delay: ${Math.round(estimatedDelay)}min`);
            
            sailingPredictions.push({
                scheduled_departure: formatTime(ferryScheduledTime),
                estimated_departure: formatTime(estimatedTime),
                estimated_delay: Math.round(estimatedDelay),
                vessel_position: ferryAtDockData.vesselPos,
                vessel_name: ferryAtDockData.vesselData.name
            });
            
            console.log(`   ✅ Added ferry-at-dock sailing: ${formatTime(ferryScheduledTime)} → ${formatTime(estimatedTime)} (${Math.round(estimatedDelay)}min delay)`);
            
            // Update the delay tracker for this vessel
            vesselDelayTracker.set(ferryAtDockData.vesselPos, Math.round(estimatedDelay));
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
                
                // Check if we already handled this vessel's own scheduled departure
                const ferryAtDockAlreadyHandled = ferryAtDockData && 
                    sailingPredictions.some(p => p.vessel_position === ferryAtDockData.vesselPos);
                
                // PRIORITY LOGIC: If this is the first sailing and there's a ferry at dock,
                // that ferry MUST be assigned to this sailing, unless we already handled its own departure
                if (i === 0 && ferryAtDockData && ferryAtDockData.vesselData.departingTerminalId === terminalId && !ferryAtDockAlreadyHandled) {
                    // Override vessel assignment - the ferry at dock gets priority
                    vesselName = ferryAtDockData.vesselData.name;
                    estimatedDelay = ferryAtDockData.vesselData.currentDelay;
                    vesselDelayTracker.set(ferryAtDockData.vesselPos, estimatedDelay);
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
export function calculateTurnaroundTimeFromTimes(previousDepartureTime, nextDepartureTime) {
    if (!previousDepartureTime || !nextDepartureTime) return 30; // Default
    
    // Estimate crossing time (could be made route-specific)
    const crossingTime = 35; // minutes
    const arrivalTime = new Date(previousDepartureTime.getTime() + (crossingTime * 60000));
    
    // Calculate turnaround: time between arrival and next departure
    const turnaroundMs = nextDepartureTime.getTime() - arrivalTime.getTime();
    return Math.max(10, Math.round(turnaroundMs / (60 * 1000))); // Minimum 10 minutes
}
