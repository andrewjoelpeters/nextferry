import { kv } from '@vercel/kv';
import { checkCacheFlushDate } from './wsdot-api.js';

// Cache delay information for a specific trip
export async function cacheDelay(tripId, delayText) {
    try {
        // Cache for 2 hours (7200 seconds)
        await kv.set(`delay:${tripId}`, delayText, { ex: 7200 });
        console.log(`Cached delay for ${tripId}: ${delayText}`);
    } catch (error) {
        console.error('Error caching delay:', error);
    }
}

// Get cached delay information
export async function getCachedDelay(tripId) {
    try {
        const delay = await kv.get(`delay:${tripId}`);
        return delay;
    } catch (error) {
        console.error('Error getting cached delay:', error);
        return null;
    }
}

// Get all cached delays (for debugging)
export async function getAllCachedDelays() {
    try {
        const keys = await kv.keys('delay:*');
        const delays = {};
        
        for (const key of keys) {
            const value = await kv.get(key);
            delays[key] = value;
        }
        
        return delays;
    } catch (error) {
        console.error('Error getting all cached delays:', error);
        return {};
    }
}
// Cache schedule data in KV store

export async function cacheSchedule(routeId, cacheFlushDate, scheduleData) {
    try {
        const cacheKey = `${SCHEDULE_CACHE_PREFIX}${routeId}-${cacheFlushDate}`;
        // Cache for 24 hours (86400 seconds) - schedules don't change often
        await kv.set(cacheKey, scheduleData, { ex: 86400 });
        console.log(`💾 Cached schedule for route ${routeId}`);
    } catch (error) {
        console.warn('Error caching schedule:', error.message);
    }
}

const CACHE_FLUSH_DATE_KEY = 'ferry:cache_flush_date';
const SCHEDULE_CACHE_PREFIX = 'ferry:schedule:';

// Get cached schedule data from KV store
export async function getCachedSchedule(routeId, cacheFlushDate) {
    try {
        const cacheKey = `${SCHEDULE_CACHE_PREFIX}${routeId}-${cacheFlushDate}`;
        const cachedData = await kv.get(cacheKey);
        return cachedData;
    } catch (error) {
        console.warn('Error getting cached schedule:', error.message);
        return null;
    }
}

export async function cacheFlushDateInKV(flushDate) {
    try {
        await kv.set(CACHE_FLUSH_DATE_KEY, flushDate, { ex: 3600 }); // Cache for 1 hour
    } catch (error) {
        console.warn('Error caching flush date:', error.message);
    }
}

// Get cached flush date from KV store
export async function getCachedFlushDate() {
    try {
        return await kv.get(CACHE_FLUSH_DATE_KEY);
    } catch (error) {
        console.warn('Error getting cached flush date:', error.message);
        return null;
    }
}

export async function maybeRefreshCache(apiKey) {
    const [current, last] = await Promise.all([
        checkCacheFlushDate(apiKey),
        getCachedFlushDate()
    ]);

    console.log(`🔍 Cache comparison:\n  Last: ${last}\n  Current: ${current}`);

    const shouldRefresh = !last || current !== last;
    if (shouldRefresh && current) {
        console.log('📅 Refreshing schedule cache in KV store');
        await cacheFlushDateInKV(current);
    } else {
        console.log('✅ Using cached schedule data');
    }

    return current;
}
