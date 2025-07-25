import { fetchSchedulesWithTimeout, generatePredictions } from './schedule-fetcher.js';
import { maybeRefreshCache } from './kv-helpers.js'
import { getRoutes } from './wsdot-api.js';

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

// Main Internal Prediction Orchestrator 
async function predictNextSailingsInternal(apiKey, vessels, routeAbbrev = null) {
    try {
        console.log('🚢 Starting predictNextSailings...');
        const overallStart = Date.now();

        const currentCacheFlushDate = await maybeRefreshCache(apiKey);
        const routes = await getRoutes(apiKey);
        const routesToCheck = routeAbbrev ? [routeAbbrev] : Object.keys(routes);

        const scheduleResults = await fetchSchedulesWithTimeout(apiKey, routes, routesToCheck, currentCacheFlushDate);
        const { cachedCount, fetchedCount, failedCount, scheduleTime } = summarizeScheduleResults(scheduleResults);

        const predictionResults = await generatePredictions(scheduleResults, vessels);
        const predictionTime = Date.now() - (overallStart + scheduleTime);

        const predictions = buildPredictionObject(predictionResults, routes);

        logPerformanceSummary({
            overallStart,
            scheduleTime,
            predictionTime,
            cachedCount,
            scheduleCount: scheduleResults.length,
            successCount: Object.keys(predictions).length,
            totalRoutes: routesToCheck.length
        });

        return predictions;
    } catch (error) {
        console.error('❌ Error predicting sailings:', error);
        throw error;
    }
}

/**
 * Summarizes schedule fetching outcomes.
 */
function summarizeScheduleResults(results) {
    const cachedCount = results.filter(r => r.fromCache).length;
    const fetchedCount = results.filter(r => !r.fromCache && r.schedule).length;
    const failedCount = results.filter(r => r.error).length;
    const scheduleTime = results.reduce((sum, r) => sum + (r.duration || 0), 0); // Optional timing logic

    console.log(`📊 Schedules: ${cachedCount} cached, ${fetchedCount} fetched, ${failedCount} failed`);

    return { cachedCount, fetchedCount, failedCount, scheduleTime };
}

/**
 * Formats prediction results into final return structure.
 */
function buildPredictionObject(predictionResults, routes) {
    const predictions = {};
    for (const { route, predictions: preds, terminalCount } of predictionResults) {
        if (terminalCount > 0) {
            predictions[route] = {
                name: routes[route]?.name || route,
                terminals: preds
            };
        }
    }
    return predictions;
}

/**
 * Logs a performance summary to console.
 */
function logPerformanceSummary({ overallStart, scheduleTime, predictionTime, cachedCount, scheduleCount, successCount, totalRoutes }) {
    const totalTime = Date.now() - overallStart;
    console.log(`\n📊 PERFORMANCE SUMMARY:`);
    console.log(`  Total time: ${totalTime}ms`);
    console.log(`  Schedule fetching: ${scheduleTime}ms`);
    console.log(`  Prediction calculations: ${predictionTime}ms`);
    console.log(`  Cache efficiency: ${cachedCount}/${scheduleCount}`);
    console.log(`  Success rate: ${successCount}/${totalRoutes}`);
}
