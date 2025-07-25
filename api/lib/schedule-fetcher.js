import { getRouteSchedule } from './wsdot-api.js';
import { cacheSchedule, getCachedSchedule } from './kv-helpers.js';
import { predictRouteNext } from './sailing-predictor.js';

/**
 * Fetches route schedules in parallel with caching and a global timeout.
 */
export async function fetchSchedulesWithTimeout(apiKey, routes, routesToCheck, flushDate) {
    const start = Date.now();
    const TIMEOUT = 15000;

    const promises = routesToCheck
        .filter(route => routes[route])
        .map(route => fetchSingleSchedule(apiKey, routes[route].id, route, flushDate));

    try {
        return await Promise.race([
            Promise.all(promises),
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Schedule fetching timeout')), TIMEOUT)
            )
        ]);
    } catch {
        console.warn('⚠️ Timeout — falling back to partial results');
        const settled = await Promise.allSettled(promises);
        return settled.map(r =>
            r.status === 'fulfilled' ? r.value : { route: 'unknown', schedule: null, error: 'timeout' }
        );
    }
}

/**
 * Fetches a schedule for a single route, checking cache first.
 */
async function fetchSingleSchedule(apiKey, routeId, route, flushDate) {
    const cached = await getCachedSchedule(routeId, flushDate);
    if (cached) return { route, schedule: cached, fromCache: true };

    try {
        const schedule = await getRouteSchedule(apiKey, routeId);
        cacheSchedule(routeId, flushDate, schedule); // fire-and-forget
        return { route, schedule, fromCache: false };
    } catch (error) {
        console.warn(`❌ Failed to fetch schedule for ${route}:`, error.message);
        return { route, schedule: null, error: error.message };
    }
}

/**
 * Generates sailing predictions for all valid schedules.
 */
export async function generatePredictions(scheduleResults, vessels) {
    const start = Date.now();
    const predictions = await Promise.all(scheduleResults
        .filter(r => r.schedule)
        .map(async ({ route, schedule }) => {
            try {
                const preds = await predictRouteNext(vessels, schedule, route);
                return { route, predictions: preds, terminalCount: Object.keys(preds).length };
            } catch (error) {
                console.warn(`Prediction failed for ${route}:`, error.message);
                return { route, predictions: {}, terminalCount: 0 };
            }
        }));
    const duration = Date.now() - start;
    predictions.duration = duration;
    return predictions;
}
