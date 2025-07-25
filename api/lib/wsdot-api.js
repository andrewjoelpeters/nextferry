import { kv } from '@vercel/kv';
import { cacheDelay, getCachedDelay } from './kv-helpers.js';

// -------------------- Utility Functions --------------------

export function parseFerryTime(msDateString) {
    if (!msDateString) return null;
    const match = msDateString.match(/\/Date\((\d+)/);
    return match ? new Date(parseInt(match[1])) : null;
}

export function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true,
        timeZone: 'America/Los_Angeles' // Force Pacific Time for ferry schedules
    });
}

export function calculateDelay(expectedTimeString, actualTimeString) {
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

export function fetchWithTimeout(url, options = {}, timeoutMs = 10000) {
    return Promise.race([
        fetch(url, options),
        new Promise((_, reject) => 
            setTimeout(() => reject(new Error(`Request timeout after ${timeoutMs}ms`)), timeoutMs)
        )
    ]);
}

// Simplified ferry API calls with timeout and retry
export async function fetchWithRetry(url, retries = 2, timeoutMs = 10000) {
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

// Parse .NET JSON date format like /Date(1753069201237-0700)/
export function parseDotNetDate(dateString) {
    if (typeof dateString !== 'string') return dateString;
    const match = dateString.match(/\/Date\((\d+)([+-]\d{4})?\)\//); 
    if (match) {
        const timestamp = parseInt(match[1]);
        return new Date(timestamp).toISOString();
    }
    return dateString;
}

// -------------------- API Fetchers --------------------

export async function getCurrentVessels(apiKey) {
    const start = Date.now();
    const url = `https://www.wsdot.wa.gov/ferries/api/vessels/rest/vessellocations?apiaccesscode=${apiKey}`;
    console.log('🚢 Fetching vessel locations from WSDOT API...');
    const data = await fetchWithRetry(url);
    const filtered = data.filter(ferry => ferry.InService && ferry.OpRouteAbbrev?.length > 0);
    const time = Date.now() - start;
    console.log(`  ✅ Vessel locations: ${time}ms (${data.length} total, ${filtered.length} in service)`);
    return filtered;
}

export async function getRouteSchedule(apiKey, routeId) {
    const start = Date.now();
    const url = `https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/${routeId}/false?apiaccesscode=${apiKey}`;
    console.log(`    📅 Fetching schedule for route ID ${routeId}...`);
    const result = await fetchWithRetry(url);
    const time = Date.now() - start;
    console.log(`    ✅ Schedule fetched: ${time}ms`);
    return result;
}

export async function getRoutes(apiKey) {
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

// Check if WSDOT schedule data has been updated
export async function checkCacheFlushDate(apiKey) {
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


// -------------------- Vessel Processor --------------------

// Unified vessel processing - fetches vessels and processes delays consistently
export async function getVesselsWithDelays(apiKey) {
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
