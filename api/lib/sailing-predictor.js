import { parseFerryTime, formatTime } from './wsdot-api.js';
import { filterRouteVessels, buildVesselInfoMap, findCurrentFerry } from './vessel-processor.js';

export function getUpcomingSailings(combo) {
    return combo.Times
        ?.map(t => ({ ...t, departTime: parseFerryTime(t.DepartingTime) }))
        .filter(t => t.departTime)
        .sort((a, b) => a.departTime - b.departTime) || [];
}

function predictSailingsForTerminal(combo, vesselInfo, now) {
    const terminalId = combo.DepartingTerminalID;
    const terminalName = combo.DepartingTerminalName;
    const allSailings = getUpcomingSailings(combo);

    if (!allSailings.length) return null;

    const predictions = [];
    const delayTracker = new Map();

    const currentFerry = findCurrentFerry(vesselInfo, terminalId);
    let currentIndex = 0;

    if (currentFerry) {
        const idx = allSailings.findIndex(s =>
            Math.abs(s.departTime - currentFerry.scheduledDeparture) < 60000
        );
        currentIndex = idx >= 0 ? idx : 0;
    }

    const upcoming = allSailings.slice(currentIndex, currentIndex + 4);

    const ferryAtDockEntry = [...vesselInfo.entries()].find(([_, v]) =>
        v.atDock && v.departingTerminalId === terminalId && !v.hasLeftDock
    );

    if (ferryAtDockEntry) {
        const [pos, data] = ferryAtDockEntry;
        const current = new Date();
        const timeSince = (current - data.scheduledDeparture) / 60000;
        const estDelay = Math.max(data.currentDelay, timeSince);
        const estTime = new Date(current.getTime());

        predictions.push({
            scheduled_departure: formatTime(data.scheduledDeparture),
            estimated_departure: formatTime(estTime),
            estimated_delay: Math.round(estDelay),
            vessel_position: pos,
            vessel_name: data.name
        });

        delayTracker.set(pos, Math.round(estDelay));
    }

    for (let i = 0; i < Math.min(upcoming.length, 3); i++) {
        const sailing = upcoming[i];
        const pos = sailing.VesselPositionNum;
        const sched = parseFerryTime(sailing.DepartingTime);
        const vessel = vesselInfo.get(pos);
        let delay = 0, name = null;

        if (vessel) {
            name = vessel.name;

            if (i === 0 && ferryAtDockEntry && ferryAtDockEntry[0] !== pos) {
                delay = ferryAtDockEntry[1].currentDelay;
                name = ferryAtDockEntry[1].name;
            } else {
                const base = vessel.currentDelay;
                const turnaround = calculateTurnaroundTimeFromTimes(vessel.scheduledDeparture, sched);
                const prev = delayTracker.get(pos) || 0;
                delay = Math.max(base, prev) + Math.max(0, base - turnaround);
            }

            delayTracker.set(pos, delay);
        } else {
            name = `Position ${pos}`;
            delay = 0;
        }

        const estTime = new Date(sched.getTime() + delay * 60000);

        // Blocking delay from previous
        if (i > 0 && predictions[i - 1].estimated_delay > 10) {
            const prevTime = parseFerryTime(upcoming[i - 1].DepartingTime);
            const prevEst = new Date(prevTime.getTime() + predictions[i - 1].estimated_delay * 60000);
            if (prevEst > sched) {
                const blockDelay = Math.round((prevEst - sched) / 60000) + 5;
                delay = Math.max(delay, blockDelay);
            }
        }

        predictions.push({
            scheduled_departure: formatTime(sched),
            estimated_departure: formatTime(estTime),
            estimated_delay: delay,
            vessel_position: pos,
            vessel_name: name
        });
    }

    return { terminal_name: terminalName, sailings: predictions };
}

export async function predictRouteNext(vessels, schedule, routeAbbrev) {
    const now = new Date();
    const routeVessels = filterRouteVessels(vessels, routeAbbrev);
    if (!routeVessels.length) return {};

    const vesselInfo = buildVesselInfoMap(routeVessels);
    const predictions = {};

    for (const combo of schedule.TerminalCombos || []) {
        const result = predictSailingsForTerminal(combo, vesselInfo, now);
        if (result) predictions[combo.DepartingTerminalID] = result;
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
