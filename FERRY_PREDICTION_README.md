# Ferry ETA Prediction System

## Overview

This document explains how the ferry tracking application predicts the next three estimated departure times for any given terminal, using the Seattle-Bainbridge route as a detailed example.

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend       │    │   WSDOT API     │
│   (script.js)   │───▶│  (ferries.js)    │───▶│   Endpoints     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌────────▼────────┐             │
         │              │  Vercel KV      │             │
         │              │  Cache Store    │             │
         │              └─────────────────┘             │
         │                                              │
         └──────────────── Combined Response ◀──────────┘
```

## Data Flow Process

### Step 1: Initial Data Gathering
**Function**: `getVesselsWithDelays(apiKey)`

```javascript
// Located in ferries.js, lines ~160-200
async function getVesselsWithDelays(apiKey) {
    // Fetches current vessel positions from WSDOT
    // Processes delay information for each ferry
    // Returns vessels with cached delay data
}
```

**What happens:**
1. Calls WSDOT vessel positions API once
2. For each ferry, calculates or retrieves cached delay information
3. Stores delay data in Vercel KV store for future use
4. Returns processed vessel data with delay information

### Step 2: Prediction Orchestration
**Function**: `predictNextSailings(apiKey, vessels, routeAbbrev)`

```javascript
// Located in ferries.js, lines ~240-250
async function predictNextSailings(apiKey, vessels, routeAbbrev = null) {
    // Orchestrates the entire prediction process
    // Includes timeout protection (25 seconds max)
    // Calls predictNextSailingsInternal for actual logic
}
```

**Key features:**
- Timeout protection to prevent Vercel function timeouts
- Processes all routes or specific route if provided
- Returns predictions for multiple routes simultaneously

### Step 3: Cache Management
**Functions**: `checkCacheFlushDate()`, `getCachedSchedule()`, `cacheSchedule()`

```
Cache Decision Flow:
┌─────────────────┐
│ Check WSDOT     │
│ Cache Flush Date│
└─────────┬───────┘
          │
          ▼
┌─────────────────┐    Yes    ┌─────────────────┐
│ Data Changed?   │──────────▶│ Fetch Fresh     │
│                 │           │ Schedules       │
└─────────┬───────┘           └─────────────────┘
          │ No
          ▼
┌─────────────────┐
│ Use Cached      │
│ Schedules       │
└─────────────────┘
```

### Step 4: Schedule Data Retrieval
**Function**: `fetchWithRetry()` with parallel processing

For Seattle-Bainbridge (route ID: 1), the system:
1. Checks KV cache first using key: `ferry:schedule:1-{cacheFlushDate}`
2. If not cached, fetches from: `https://www.wsdot.wa.gov/ferries/api/schedule/rest/scheduletoday/1/true`
3. Applies 6-second timeout per request with 1 retry
4. Caches result in KV store for 24 hours

### Step 5: Route-Specific Prediction
**Function**: `predictRouteNext(vessels, schedule, routeAbbrev)`

This is where the magic happens for each route:

```
Seattle-Bainbridge Route Processing:
┌─────────────────────────────────────────────────────────────┐
│                    Route: sea-bi                            │
├─────────────────────────────────────────────────────────────┤
│ Terminals:                                                  │
│ • Seattle (Terminal ID: 1) → Bainbridge (Terminal ID: 3)   │
│ • Bainbridge (Terminal ID: 3) → Seattle (Terminal ID: 1)   │
└─────────────────────────────────────────────────────────────┘
```

#### Step 5a: Vessel Analysis
```javascript
// Create vessel information map with current status
const vesselInfo = new Map();

routeVessels.forEach(vessel => {
    // For each ferry on the Seattle-Bainbridge route:
    // - Calculate current delay (if departed) or use cached delay
    // - Track scheduled departure time
    // - Note if ferry is at dock or has left dock
    // - Store departing terminal ID
});
```

#### Step 5b: Critical Ferry-at-Dock Logic
```javascript
// CRITICAL: Check if any ferry is at the dock
let ferryAtDock = null;
for (const [vesselPos, vesselData] of vesselInfo) {
    if (vesselData.atDock && vesselData.departingTerminalId === terminalId && !vesselData.hasLeftDock) {
        ferryAtDock = { vesselPos, vesselData };
        break;
    }
}
```

**Priority Rule**: If a ferry is physically at the dock, it MUST be the next departure, regardless of schedule timing or delays.

#### Step 5c: Terminal Processing
For each terminal (Seattle and Bainbridge):

1. **Get Upcoming Sailings**:
   ```javascript
   const upcomingSailings = combo.Times
       ?.filter(time => {
           const departTime = parseFerryTime(time.DepartingTime);
           return departTime && departTime > now; // Only future departures
       })
       .sort((a, b) => { /* Sort by departure time */ })
       .slice(0, 4); // Get next 4 sailings
   ```

2. **Process Next 3 Departures**:
   ```
   For Seattle Terminal:
   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
   │   Next Sailing  │    │  2nd Sailing    │    │  3rd Sailing    │
   │                 │    │                 │    │                 │
   │ Ferry at dock?  │    │ Apply delay     │    │ Propagate       │
   │ → Use its delay │    │ propagation     │    │ delays          │
   │                 │    │                 │    │                 │
   │ Vessel: Tacoma  │    │ Vessel: Spokane │    │ Vessel: Tacoma  │
   │ Delay: 15 min   │    │ Delay: 12 min   │    │ Delay: 8 min    │
   └─────────────────┘    └─────────────────┘    └─────────────────┘
   ```

#### Step 5d: Delay Calculation Logic

**For Ferry at Dock** (Highest Priority):
```javascript
if (i === 0 && ferryAtDock && ferryAtDock.vesselData.departingTerminalId === terminalId) {
    vesselName = ferryAtDock.vesselData.name;
    estimatedDelay = ferryAtDock.vesselData.currentDelay;
}
```

**For Ferry That Has Departed** (Delay Propagation):
```javascript
if (vessel.hasLeftDock) {
    const turnaroundTime = calculateTurnaroundTimeFromTimes(previousSailingTime, scheduledTime);
    
    if (turnaroundTime < 25) {
        estimatedDelay = Math.max(0, vessel.currentDelay * 0.95); // 95% delay carries over
    } else if (turnaroundTime < 45) {
        estimatedDelay = Math.max(0, vessel.currentDelay * 0.9);  // 90% delay carries over
    } else {
        estimatedDelay = Math.max(0, vessel.currentDelay * 0.8);  // 80% delay carries over
    }
}
```

**Delay Propagation Rules**:
- **Short turnaround** (<25 min): 95% of delay carries forward
- **Normal turnaround** (25-45 min): 90% of delay carries forward  
- **Long turnaround** (>45 min): 80% of delay carries forward

#### Step 5e: Blocking Delay Logic
```javascript
// Handle blocking delays from previous sailings
if (i > 0) {
    const previousSailing = sailingPredictions[i - 1];
    const timeBetweenSailings = (scheduledTime - previousScheduledTime) / (60 * 1000);
    
    if (previousSailing.estimatedDelay > timeBetweenSailings) {
        // Previous sailing's delay blocks this one
        const blockingDelay = previousSailing.estimatedDelay - timeBetweenSailings;
        estimatedDelay = Math.max(estimatedDelay, blockingDelay);
    }
}
```

## Example: Seattle Terminal Prediction

Let's trace through a real example for Seattle Terminal at 2:30 PM:

### Current State:
- **Ferry Tacoma**: At Seattle dock, scheduled 2:25 PM departure, 15 minutes late
- **Ferry Spokane**: En route to Bainbridge, departed Seattle at 1:30 PM (10 min late)
- **Ferry Wenatchee**: At Bainbridge dock

### Schedule:
- 2:25 PM departure (Tacoma) 
- 3:15 PM departure (Spokane)
- 4:05 PM departure (Tacoma)

### Prediction Results:

**1st Departure (2:25 PM scheduled)**:
- **Ferry**: Tacoma (at dock - PRIORITY)
- **Estimated Time**: 2:40 PM (15 min delay)
- **Status**: "Departing Now" or "15m late"

**2nd Departure (3:15 PM scheduled)**:
- **Ferry**: Spokane (returning from Bainbridge)
- **Turnaround**: ~45 minutes (normal)
- **Delay Propagation**: 10 min × 0.9 = 9 minutes
- **Estimated Time**: 3:24 PM

**3rd Departure (4:05 PM scheduled)**:
- **Ferry**: Tacoma (returning from Bainbridge)  
- **Turnaround**: ~85 minutes (long)
- **Delay Propagation**: 15 min × 0.8 = 12 minutes
- **Estimated Time**: 4:17 PM

## Frontend Display

**Function**: `updateNextSailingsList()` in script.js

The frontend receives this data and displays:

```
Seattle Terminal → Bainbridge Island
┌─────────────────────────────────────────┐
│ 🚢 Tacoma                              │
│ Now departing (15m late)                │
│ Scheduled: 2:25 PM | Est: 2:40 PM      │
├─────────────────────────────────────────┤
│ 🚢 Spokane                             │
│ 54m (9m late)                          │
│ Scheduled: 3:15 PM | Est: 3:24 PM      │
├─────────────────────────────────────────┤
│ 🚢 Tacoma                              │
│ 1h 47m (12m late)                      │
│ Scheduled: 4:05 PM | Est: 4:17 PM      │
└─────────────────────────────────────────┘
```

## Performance Optimizations

### Caching Strategy:
- **Schedule Data**: 24-hour cache in Vercel KV
- **Cache Flush Detection**: 1-hour cache, checks WSDOT for updates
- **Vessel Delays**: 2-hour cache for departed ferries

### Timeout Protection:
- **Individual API calls**: 6-second timeout
- **Overall function**: 25-second timeout (5s buffer for Vercel's 30s limit)
- **Parallel processing**: All route schedules fetched simultaneously

### Error Handling:
- **Graceful degradation**: Shows partial data if some routes fail
- **Retry logic**: 1 retry for failed schedule fetches
- **Fallback data**: Uses cached data when fresh data unavailable

## Key Functions Reference

| Function | Purpose | Location |
|----------|---------|----------|
| `getVesselsWithDelays()` | Fetch vessel positions with delay processing | ferries.js:160 |
| `predictNextSailings()` | Main prediction orchestrator | ferries.js:240 |
| `predictRouteNext()` | Route-specific prediction logic | ferries.js:395 |
| `checkCacheFlushDate()` | Cache invalidation check | ferries.js:217 |
| `fetchWithRetry()` | API call with timeout/retry | ferries.js:58 |
| `calculateDelay()` | Delay calculation from timestamps | ferries.js:25 |
| `updateNextSailingsList()` | Frontend display update | script.js:350 |

This system provides accurate, real-time ferry predictions by combining live vessel data, schedule information, and intelligent delay propagation algorithms while maintaining high performance through aggressive caching and timeout management.
