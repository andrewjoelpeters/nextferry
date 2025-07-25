import { getVesselsWithDelays } from './lib/wsdot-api.js';
import { predictNextSailings } from './lib/prediction-orchestrator.js';

const DEFAULT_DISPLAYED_ROUTES = ['sea-bi', 'ed-king'];

export default async function handler(req, res) {
    try {
        res.setHeader('Access-Control-Allow-Origin', '*');
        res.setHeader('Access-Control-Allow-Methods', 'GET');
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

        const apiKey = process.env.WSDOT_API_KEY;
        if (!apiKey) {
            return res.status(500).json({ error: 'API key missing' });
        }

        const { route, routes } = req.query;

        let routesToProcess;
        if (route) {
            routesToProcess = [route];
        } else if (routes) {
            routesToProcess = routes.split(',').map(r => r.trim());
        } else {
            routesToProcess = DEFAULT_DISPLAYED_ROUTES;
        }

        console.log(`🎯 Processing routes: ${routesToProcess.join(', ')}`);

        const vessels = await getVesselsWithDelays(apiKey);

        const predictions = {};
        for (const routeAbbrev of routesToProcess) {
            const routePredictions = await predictNextSailings(apiKey, vessels, routeAbbrev);
            if (routePredictions && Object.keys(routePredictions).length > 0) {
                Object.assign(predictions, routePredictions);
            }
        }

        res.status(200).json({
            type: 'combined',
            vessels,
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
