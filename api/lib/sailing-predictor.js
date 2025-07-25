import { parseFerryTime, formatTime } from './wsdot-api.js';
import { filterRouteVessels, buildVesselInfoMap, findCurrentFerry } from './vessel-processor.js';

export function getUpcomingSailings(combo) {
    const sailings = combo.Times
        ?.map(t => ({ ...t, departTime: parseFerryTime(t.DepartingTime) }))
        .filter(t => t.departTime)
        .sort((a, b) => a.departTime - b.departTime) || [];

    console.log(`📅 Found ${sailings.length} upcoming sailings for terminal ${combo.DepartingTerminalName}`);
    return sailings;
}

function predictSailingsForTerminal(combo, vesselInfo, now) {
    const terminalId = combo.DepartingTerminalID;
    const terminalName = combo.DepartingTerminalName;
    const allSailings = getUpcomingSailings(combo);

    if (!allSailings.length) {
        console.log(`⚠️ No sailings found for terminal ${terminalName} (${terminalId})`);
        return null;
    }

    const predictions = [];
    const delayTracker = new Map();

    const currentFerry = findCurrentFerry(vesselInfo, terminalId);
    let currentIndex = 0;

    if (currentFerry) {
        const idx = allSailings.findIndex(s =>
            Math.abs(s.departTime - currentFerry.scheduledDeparture) < 60000
        );
        currentIndex = idx >= 0 ? idx : 0;
        console.log(`🚢 Current ferry found at terminal ${terminalName} (position ${currentFerry.positionNum}): scheduled departure ${formatTime(currentFerry.scheduledDeparture)}, matching index: ${idx}`);
    } else {
        console.log(`❌ No current ferry detected at terminal ${terminalName}`);
    }

    const upcoming = allSailings.slice(currentIndex, currentIndex + 4);
    console.log(`🔮 Predicting up to 4 sailings from index ${currentIndex} (${upcoming.length} found)`);

    const ferryAtDockEntry = [...vesselInfo.entries()].find(([_, v]) =>
        v.atDock && v.departingTerminalId === terminalId && !v.hasLeftDock
    );

    if (ferryAtDockEntry) {
        const [pos, data] = ferryAtDockEntry;
        const current = new Date();
        const timeSince = (current - data.scheduledDeparture) / 60000;
        const estDelay = Math.max(data.currentDelay, timeSince);
        const estTime = new Date(current.getTime());

        console.log(`🛳️ Ferry at dock (position ${pos}, name: ${data.name}):`);
        console.log(`   Scheduled departure: ${formatTime(data.scheduledDeparture)}`);
        console.log(`   Time since sched: ${timeSince.toFixed(1)} min, Reported delay: ${data.currentDelay}, Using est. delay: ${Math.round(estDelay)}`);

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
                console.log(`⛴️ First sailing mismatch: using delay from ferry at dock (pos ${ferryAtDockEntry[0]}) instead of ${pos}`);
            } else {
                const base = vessel.currentDelay;
                const turnaround = calculateTurnaroundTimeFromTimes(vessel.scheduledDeparture, sched);
                const prev = delayTracker.get(pos) || 0;
                delay = Math.max(base, prev) + Math.max(0, base - turnaround);

                console.log(`🕐 Calculating delay for vessel ${name} (position ${pos}):`);
                console.log(`   Base delay: ${base}, Prev delay: ${prev}, Turnaround time: ${turnaround}`);
                console.log(`   Final delay: ${delay}`);
            }

            delayTracker.set(pos, delay);
        } else {
            name = `Position ${pos}`;
            delay = 0;
            console.log(`❓ No vessel info for position ${pos}, assuming no delay`);
        }

        let estTime = new Date(sched.getTime() + delay * 60000);

        if (i > 0 && predictions[i - 1].estimated_delay > 10) {
            const prevTime = parseFerryTime(upcoming[i - 1].DepartingTime);
            const prevEst = new Date(prevTime.getTime() + predictions[i - 1].estimated_delay * 60000);
            if (prevEst > sched) {
                const blockDelay = Math.round((prevEst - sched) / 60000) + 5;
                console.log(`⛔ Blocking delay applied: previous est ${formatTime(prevEst)} > current sched ${formatTime(sched)}, adding ${blockDelay} min`);
                delay = Math.max(delay, blockDelay);
                estTime = new Date(sched.getTime() + delay * 60000);
            }
        }

        predictions.push({
            scheduled_departure: formatTime(sched),
            estimated_departure: formatTime(estTime),
            estimated_delay: delay,
            vessel_position: pos,
            vessel_name: name
        });

        console.log(`✅ Predicted sailing ${i + 1} for ${terminalName}:`);
        console.log(`   Scheduled: ${formatTime(sched)}, Estimated: ${formatTime(estTime)}, Delay: ${delay} min, Vessel: ${name}`);
    }

    return { terminal_name: terminalName, sailings: predictions };
}

export async function predictRouteNext(vessels, schedule, routeAbbrev) {
    const now = new Date();
    console.log(`🔍 Predicting sailings for route: ${routeAbbrev}`);
    const routeVessels = filterRouteVessels(vessels, routeAbbrev);
    console.log(`🧭 Found ${routeVessels.length} vessels on this route`);

    if (!routeVessels.length) return {};

    const vesselInfo = buildVesselInfoMap(routeVessels);
    const predictions = {};

    for (const combo of schedule.TerminalCombos || []) {
        console.log(`➡️ Predicting direction: ${combo.Abbrev} (${combo.DepartingTerminalName} to ${combo.ArrivingTerminalName})`);
        const result = predictSailingsForTerminal(combo, vesselInfo, now);
        if (result) {
            predictions[combo.DepartingTerminalID] = result;
            console.log(`📌 Added prediction for terminal ${combo.DepartingTerminalName}`);
        } else {
            console.log(`❌ Skipping terminal ${combo.DepartingTerminalName}, no valid sailings`);
        }
    }

    return predictions;
}

export function calculateTurnaroundTimeFromTimes(previousDepartureTime, nextDepartureTime) {
    if (!previousDepartureTime || !nextDepartureTime) {
        console.log(`⚙️ Using default turnaround time (30 min)`);
        return 30;
    }

    const crossingTime = 35; // minutes
    const arrivalTime = new Date(previousDepartureTime.getTime() + (crossingTime * 60000));
    const turnaroundMs = nextDepartureTime.getTime() - arrivalTime.getTime();
    const turnaround = Math.max(10, Math.round(turnaroundMs / (60 * 1000)));

    console.log(`🔁 Calculated turnaround time: ${turnaround} min (arrival: ${formatTime(arrivalTime)}, next depart: ${formatTime(nextDepartureTime)})`);
    return turnaround;
}
