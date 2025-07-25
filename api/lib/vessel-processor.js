import { parseFerryTime, calculateDelay } from './wsdot-api.js';

export function filterRouteVessels(vessels, routeAbbrev) {
    return vessels.filter(v => v.OpRouteAbbrev?.includes(routeAbbrev));
}

export function buildVesselInfoMap(vessels) {
    const info = new Map();
    for (const vessel of vessels) {
        const pos = vessel.VesselPositionNum;
        if (!pos || !vessel.ScheduledDeparture) continue;

        let delay = 0;
        if (vessel.LeftDock) {
            const { delayMinutes, error } = calculateDelay(vessel.ScheduledDeparture, vessel.LeftDock);
            if (!error) delay = delayMinutes;
        } else if (vessel.cachedDelay) {
            const match = vessel.cachedDelay.match(/(\d+)\s*min\s*(late|early)/);
            if (match) delay = match[2] === 'late' ? +match[1] : -match[1];
        }

        info.set(pos, {
            name: vessel.VesselName,
            currentDelay: delay,
            scheduledDeparture: parseFerryTime(vessel.ScheduledDeparture),
            hasLeftDock: vessel.LeftDock !== null,
            departingTerminalId: vessel.DepartingTerminalID,
            atDock: vessel.AtDock
        });
    }
    return info;
}

export function findCurrentFerry(vesselInfo, terminalId) {
    const values = [...vesselInfo.values()];
    const atDock = values.find(v => v.atDock && v.departingTerminalId === terminalId && !v.hasLeftDock);
    if (atDock) return atDock;

    const enRoute = values
        .filter(v => v.arrivingTerminalId === terminalId && !v.atDock)
        .sort((a, b) => (a.eta ?? Infinity) - (b.eta ?? Infinity));

    return enRoute[0] ?? null;
}
