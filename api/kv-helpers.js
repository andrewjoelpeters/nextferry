import { kv } from '@vercel/kv';

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
