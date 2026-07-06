"""Generate self-contained HTML viewer for 3 bad prediction cases."""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

# Reuse the analysis script's prediction logic
from backend.database import get_connection, init_db
from scripts.analyze_prediction_outliers import (
    _compute_delay_from_snapshot,
    predict_option_a,
)

CASES = [
    {
        "vessel": "Puyallup",
        "sched": "2026-06-24T13:35:00-07:00",
        "label": "Puyallup @ 13:35 PT — Overprediction (+62m)",
        "note": "Despite a 52m cascade delay, Option A predicted 115m because the inbound vessel's ETA kept slipping. The ETA was pessimistic vs actual arrival, causing the overprediction.",
    },
    {
        "vessel": "Tacoma",
        "sched": "2026-06-27T16:40:00-07:00",
        "label": "Tacoma @ 16:40 PT — Underprediction (-60m)",
        "note": "Runaway cascade: previous sailings were 28m, 45m, 54m, 60m late. Option A predicted 0-1m because WSDOT ETA said the vessel would arrive early enough for turnaround. The ETA was wrong.",
    },
    {
        "vessel": "Wenatchee",
        "sched": "2026-07-02T14:55:00-07:00",
        "label": "Wenatchee @ 14:55 PT — Underprediction (-48m)",
        "note": "Similar cascade failure: consistent 43-48m delays from earlier in the day. Option A trusted ETA and predicted 0m at T-45/T-60, missing the building cascade entirely.",
    },
]

TERMINALS = {
    "Seattle": {"lat": 47.6027, "lon": -122.3388},
    "Bainbridge Island": {"lat": 47.6262, "lon": -122.5204},
    "Edmonds": {"lat": 47.8115, "lon": -122.3832},
    "Kingston": {"lat": 47.7984, "lon": -122.4982},
    "Mukilteo": {"lat": 47.9491, "lon": -122.3045},
    "Clinton": {"lat": 47.9771, "lon": -122.3555},
    "Fauntleroy": {"lat": 47.5237, "lon": -122.3937},
    "Southworth": {"lat": 47.5122, "lon": -122.5008},
    "Vashon": {"lat": 47.4471, "lon": -122.4599},
    "Port Townsend": {"lat": 48.1154, "lon": -122.7603},
    "Coupeville": {"lat": 48.2206, "lon": -122.6854},
    "Anacortes": {"lat": 48.5178, "lon": -122.6078},
    "Friday Harbor": {"lat": 48.5355, "lon": -123.0155},
    "Sidney BC": {"lat": 48.6486, "lon": -123.4004},
    "Orcas": {"lat": 48.7045, "lon": -122.9123},
    "San Juan": {"lat": 48.5349, "lon": -123.0178},
    "Shaw": {"lat": 48.5741, "lon": -122.9353},
    "Lopez": {"lat": 48.4829, "lon": -122.8954},
    "Point Defiance": {"lat": 47.3078, "lon": -122.5153},
    "Tahlequah": {"lat": 47.3333, "lon": -122.5067},
}


def get_chain(conn, vessel, sched_iso):
    events = conn.execute(
        """SELECT scheduled_departure, actual_departure, delay_minutes,
                  departing_terminal_id, arriving_terminal_id, route_abbrev
           FROM sailing_events
           WHERE vessel_name=? AND route_abbrev IN ('sea-bi','ed-king')
           ORDER BY scheduled_departure""",
        (vessel,),
    ).fetchall()

    target_idx = next(
        (i for i, e in enumerate(events) if e["scheduled_departure"] == sched_iso),
        None,
    )
    if target_idx is None:
        return [], 0

    start = max(0, target_idx - 3)
    end = min(len(events), target_idx + 3)
    return events[start:end], target_idx - start


def get_snapshots(conn, vessel, sched_iso):
    sched_dt = datetime.fromisoformat(sched_iso)
    start = (sched_dt - timedelta(hours=2)).isoformat()
    end = (sched_dt + timedelta(hours=1)).isoformat()

    rows = conn.execute(
        """SELECT collected_at, latitude, longitude, speed, heading, at_dock,
                  left_dock, eta, departing_terminal_name, arriving_terminal_name,
                  departing_terminal_id, arriving_terminal_id, scheduled_departure
           FROM vessel_snapshots
           WHERE vessel_name=? AND collected_at >= ? AND collected_at <= ?
           ORDER BY collected_at""",
        (vessel, start, end),
    ).fetchall()
    return [dict(r) for r in rows]


def snap_to_pandas_series(snap: dict) -> pd.Series:
    """Convert a raw snapshot dict to a pandas Series for the analysis functions."""
    s = pd.Series(dtype=object)
    s["collected_at"] = pd.to_datetime(snap["collected_at"])
    s["scheduled_departure"] = (
        pd.to_datetime(snap["scheduled_departure"])
        if snap.get("scheduled_departure")
        else pd.NaT
    )
    s["left_dock"] = (
        pd.to_datetime(snap["left_dock"]) if snap.get("left_dock") else pd.NaT
    )
    s["eta"] = (
        pd.to_datetime(snap["eta"]) if snap.get("eta") else pd.NaT
    )
    s["at_dock"] = snap["at_dock"]
    return s


def main():
    init_db()
    conn = get_connection()

    output = {"cases": [], "terminals": TERMINALS}

    for case in CASES:
        vessel = case["vessel"]
        sched = case["sched"]

        event = conn.execute(
            """SELECT * FROM sailing_events
               WHERE vessel_name=? AND scheduled_departure=?""",
            (vessel, sched),
        ).fetchone()
        if not event:
            continue

        route = event["route_abbrev"]
        actual_delay = round(event["delay_minutes"], 1)
        sched_dt = datetime.fromisoformat(sched)

        chain, target_pos = get_chain(conn, vessel, sched)
        chain_data = [
            {
                "scheduled_departure": e["scheduled_departure"],
                "actual_departure": e["actual_departure"],
                "delay_minutes": round(e["delay_minutes"], 1),
                "departing": e["departing_terminal_id"],
                "arriving": e["arriving_terminal_id"],
            }
            for e in chain
        ]

        # Get all snapshots and compute prediction at each point
        raw_snaps = get_snapshots(conn, vessel, sched)

        # Determine if s1 is opposite terminal (for prediction logic)
        s0_arr_terminal = chain[target_pos - 1]["arriving_terminal_id"] if target_pos > 0 else None
        s1_dep_terminal = chain[target_pos]["departing_terminal_id"] if target_pos < len(chain) else None
        s1_is_opposite = (
            s0_arr_terminal is not None
            and s1_dep_terminal is not None
            and s0_arr_terminal == s1_dep_terminal
        )

        snap_data = []
        for snap in raw_snaps:
            s = snap_to_pandas_series(snap)
            current_delay = _compute_delay_from_snapshot(s, route)
            if current_delay is None:
                continue

            snap_time = pd.to_datetime(snap["collected_at"])
            minutes_before = (
                (sched_dt - snap_time.to_pydatetime()).total_seconds() / 60
            )

            # Compute both flat propagation (current production) and Option A (comparison)
            is_en_route = snap["at_dock"] == 0
            has_eta = snap["eta"] is not None and snap["eta"] != ""

            # Flat propagation is the default (matches current production)
            flat_pred = current_delay
            flat_source = "flat_propagation"

            # Option A (ETA-bounded) for comparison
            option_a_pred = None
            if is_en_route and has_eta and s1_is_opposite:
                eta_dt = pd.to_datetime(snap["eta"])
                s1_sched_pd = pd.to_datetime(sched)
                option_a_pred = round(predict_option_a(current_delay, eta_dt, s1_sched_pd, route), 1)

            snap_data.append(
                {
                    "collected_at": snap["collected_at"],
                    "lat": snap["latitude"],
                    "lon": snap["longitude"],
                    "speed": round(snap["speed"], 1) if snap["speed"] is not None else None,
                    "heading": snap["heading"],
                    "at_dock": bool(snap["at_dock"]),
                    "left_dock": snap["left_dock"],
                    "eta": snap["eta"],
                    "departing_terminal": snap["departing_terminal_name"],
                    "arriving_terminal": snap["arriving_terminal_name"],
                    "minutes_before": round(minutes_before, 0),
                    "current_delay": round(current_delay, 1),
                    "prediction": round(flat_pred, 1),
                    "option_a_prediction": option_a_pred,
                    "prediction_source": flat_source,
                }
            )

        output["cases"].append(
            {
                "label": case["label"],
                "note": case["note"],
                "vessel": vessel,
                "route": route,
                "scheduled_departure": sched,
                "actual_departure": event["actual_departure"],
                "actual_delay": actual_delay,
                "chain": chain_data,
                "chain_target_pos": target_pos,
                "snapshots": snap_data,
            }
        )

    conn.close()

    html = generate_html(output)
    out_path = Path("reports/prediction_viewer.html")
    out_path.write_text(html)
    print(f"\nViewer saved to: {out_path} ({len(html):,} bytes)")


def generate_html(data: dict[str, Any]) -> str:
    json_data = json.dumps(data, indent=2, default=str)
    json_data = json_data.replace("</script>", "<\\/script>")

    # Read template from file to avoid f-string escaping issues
    template = _TEMPLATE
    return template.replace("__JSON_DATA__", json_data)


_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ferry Prediction Explorer</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">
</script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #1a1a2e; color: #e0e0e0; height: 100vh; overflow: hidden; }
.app { display: flex; height: 100vh; }
#map { flex: 1; height: 100%; }
.panel { width: 520px; min-width: 520px; height: 100%; overflow-y: auto; padding: 20px; background: #16213e; border-left: 1px solid #0f3460; }
h1 { font-size: 18px; margin-bottom: 2px; color: #e94560; }
h2 { font-size: 13px; margin-bottom: 12px; color: #888; font-weight: normal; line-height: 1.4; }
h3 { font-size: 12px; margin: 14px 0 6px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }
.case-selector { display: flex; gap: 6px; margin-bottom: 14px; }
.case-btn { padding: 8px 12px; border-radius: 6px; border: 1px solid #0f3460; background: #1a1a2e; color: #aaa; cursor: pointer; font-size: 11px; }
.case-btn.active { background: #e94560; color: white; border-color: #e94560; }
.case-btn:hover { border-color: #e94560; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 10px; }
.info-item { background: #0f3460; padding: 8px; border-radius: 6px; text-align: center; }
.info-label { font-size: 9px; color: #888; text-transform: uppercase; }
.info-value { font-size: 20px; font-weight: bold; }
.info-value.bad { color: #e94560; }
.info-value.good { color: #4ecca3; }
.info-value.warn { color: #f0a500; }
.chain { display: flex; gap: 3px; margin-bottom: 12px; flex-wrap: wrap; }
.chain-item { padding: 3px 6px; border-radius: 4px; font-size: 10px; background: #0f3460; color: #888; text-align: center; min-width: 64px; }
.chain-item.target { background: #e94560; color: white; font-weight: 600; }
.chain-item .time { font-size: 10px; }
.chain-item .delay { font-size: 9px; margin-top: 1px; }
.controls { display: flex; gap: 6px; align-items: center; margin-bottom: 8px; }
.controls button { padding: 6px 14px; border-radius: 6px; border: 1px solid #0f3460; background: #1a1a2e; color: #e0e0e0; cursor: pointer; font-size: 13px; }
.controls button:hover { background: #0f3460; }
.controls .counter { font-size: 12px; color: #888; }
.slider { width: 100%; margin: 6px 0 10px; accent-color: #e94560; }
.detail { background: #0f3460; border-radius: 8px; padding: 10px; margin-bottom: 10px; }
.detail-row { display: flex; justify-content: space-between; padding: 3px 0; font-size: 12px; border-bottom: 1px solid #1a1a2e; }
.detail-row:last-child { border-bottom: none; }
.detail-label { color: #888; }
.detail-value { color: #e0e0e0; font-weight: 500; }
.pred-display { text-align: center; padding: 12px; background: #1a1a2e; border-radius: 8px; margin-bottom: 10px; }
.pred-value { font-size: 44px; font-weight: bold; }
.pred-value.bad { color: #e94560; }
.pred-value.good { color: #4ecca3; }
.pred-value.warn { color: #f0a500; }
.pred-unit { font-size: 13px; color: #888; }
.pred-compare { font-size: 13px; color: #888; margin-top: 3px; }
.pred-error { font-size: 15px; font-weight: 600; margin-top: 2px; }
.note { font-size: 11px; color: #777; line-height: 1.4; margin: 10px 0; padding: 10px; background: #0f3460; border-radius: 6px; border-left: 3px solid #e94560; }
.chart { margin-top: 10px; height: 100px; position: relative; background: #0f3460; border-radius: 6px; overflow: hidden; padding-top: 4px; }
.chart-bar { position: absolute; bottom: 0; width: 3px; background: #e94560; border-radius: 2px 2px 0 0; opacity: 0.7; }
.chart-bar.flat { background: #f0a500; opacity: 0.5; }
.chart-bar.current { background: #8888ff; opacity: 0.5; }
.actual-line { position: absolute; left: 0; right: 0; border-top: 2px dashed #4ecca3; opacity: 0.7; }
.actual-label { position: absolute; right: 4px; font-size: 8px; color: #4ecca3; opacity: 0.7; }
.copy { font-size: 10px; color: #444; margin-top: 16px; text-align: center; }
</style>
</head>
<body>
<div class="app">
  <div id="map"></div>
  <div class="panel" id="panel">
    <h1>Ferry Prediction Explorer</h1>
    <h2 id="case-label">Select a case below</h2>
    <div class="case-selector" id="case-selector"></div>
    <div id="content"></div>
    <div class="copy">Use arrow keys, Prev/Next buttons, or slider to step through snapshots.</div>
  </div>
</div>
<script>
const DATA = __JSON_DATA__;
let curCase = 0, curSnap = 0;
let map, vesselMarker, terminalMarkers = [], trackLines = [];

function init() {
  map = L.map('map', { zoomControl: true }).setView([47.7, -122.4], 9);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors', maxZoom: 18
  }).addTo(map);

  const sel = document.getElementById('case-selector');
  DATA.cases.forEach((c, i) => {
    const btn = document.createElement('button');
    btn.className = 'case-btn' + (i === 0 ? ' active' : '');
    btn.textContent = c.vessel + ' (' + c.route + ')';
    btn.onclick = () => selectCase(i);
    sel.appendChild(btn);
  });

  selectCase(0);
}

function selectCase(idx) {
  curCase = idx; curSnap = 0;
  document.querySelectorAll('.case-btn').forEach((b, i) => b.className = 'case-btn' + (i === idx ? ' active' : ''));
  render();
}

function render() {
  const c = DATA.cases[curCase];
  if (!c) return;
  document.getElementById('case-label').textContent = c.label;

  const content = document.getElementById('content');
  content.innerHTML = renderCaseHTML(c);

  document.getElementById('snap-slider').max = c.snapshots.length - 1;
  document.getElementById('snap-slider').value = 0;
  document.getElementById('snap-slider').oninput = e => { curSnap = +e.target.value; updateView(c); };
  document.getElementById('snap-prev').onclick = () => { if (curSnap > 0) { curSnap--; document.getElementById('snap-slider').value = curSnap; updateView(c); } };
  document.getElementById('snap-next').onclick = () => { if (curSnap < c.snapshots.length - 1) { curSnap++; document.getElementById('snap-slider').value = curSnap; updateView(c); } };
  document.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft') document.getElementById('snap-prev').click();
    if (e.key === 'ArrowRight') document.getElementById('snap-next').click();
  });

  updateView(c);
}

function renderCaseHTML(c) {
  const chain = c.chain, tp = c.chain_target_pos;
  let ch = '<div class="chain">';
  chain.forEach((e, i) => {
    const t = e.scheduled_departure.slice(11, 16);
    const cls = i === tp ? 'chain-item target' : 'chain-item';
    ch += '<div class="' + cls + '"><div class="time">' + t + '</div><div class="delay">' + e.delay_minutes + 'm</div></div>';
  });
  ch += '</div>';

  return [
    '<div class="info-grid">',
      '<div class="info-item"><div class="info-label">Actual Delay</div><div class="info-value ' + (c.actual_delay > 10 ? 'bad' : 'good') + '">' + c.actual_delay + 'm</div></div>',
      '<div class="info-item"><div class="info-label">Snapshots</div><div class="info-value">' + c.snapshots.length + '</div></div>',
      '<div class="info-item"><div class="info-label">Route</div><div class="info-value" style="font-size:14px">' + c.route + '</div></div>',
    '</div>',
    '<h3>Sailing Chain</h3>',
    ch,
    '<div class="note">' + c.note + '</div>',
    '<h3>Snapshot Timeline (T-120min to departure)</h3>',
    '<div class="controls">',
      '<button id="snap-prev">&#9664; Prev</button>',
      '<span class="counter" id="snap-counter">1 / ' + c.snapshots.length + '</span>',
      '<button id="snap-next">Next &#9654;</button>',
    '</div>',
    '<input type="range" class="slider" id="snap-slider" min="0" max="0" value="0">',
    '<div id="snapshot-display"></div>',
    '<div id="chart-container"></div>',
  ].join('\n');
}

function renderSnapshotHTML(snap, c) {
  if (!snap) return '<div class="detail">No data</div>';
  const st = snap.collected_at.slice(11, 19);
  const mb = snap.minutes_before;
  const pred = snap.prediction, cur = snap.current_delay;
  const actual = c.actual_delay;
  const err = pred - actual;
  const absErr = Math.abs(err);
  const errCls = absErr > 20 ? 'bad' : (absErr > 5 ? 'warn' : 'good');
  const errSign = err > 0 ? '+' : '';
  const optA = snap.option_a_prediction;
  const optALine = optA !== null ? '<div class="detail-row"><span class="detail-label">Option A (ETA)</span><span class="detail-value" style="color:' + (Math.abs(optA - actual) > 20 ? '#e94560' : '#888') + '">' + optA.toFixed(0) + 'm</span></div>' : '';

  return [
    '<div class="pred-display">',
      '<div class="pred-value ' + errCls + '">' + pred.toFixed(0) + '</div>',
      '<div class="pred-unit">min predicted delay (flat propagation)</div>',
      '<div class="pred-compare">Current delay: ' + cur.toFixed(1) + 'm &nbsp;|&nbsp; Actual: ' + actual + 'm</div>',
      '<div class="pred-error ' + errCls + '">' + errSign + err.toFixed(0) + 'm error</div>',
    '</div>',
    '<div class="detail">',
      '<div class="detail-row"><span class="detail-label">Time</span><span class="detail-value">' + st + ' (T-' + Math.abs(mb) + 'min)</span></div>',
      '<div class="detail-row"><span class="detail-label">At Dock</span><span class="detail-value">' + (snap.at_dock ? 'Yes' : 'En-route') + '</span></div>',
      '<div class="detail-row"><span class="detail-label">Speed</span><span class="detail-value">' + (snap.speed !== null ? snap.speed + ' kn' : '?') + '</span></div>',
      '<div class="detail-row"><span class="detail-label">Heading</span><span class="detail-value">' + (snap.heading !== null ? snap.heading + '&#176;' : '?') + '</span></div>',
      '<div class="detail-row"><span class="detail-label">Position</span><span class="detail-value">' + (snap.lat !== null ? snap.lat.toFixed(4) + ', ' + snap.lon.toFixed(4) : '?') + '</span></div>',
      '<div class="detail-row"><span class="detail-label">WSDOT ETA</span><span class="detail-value">' + (snap.eta ? snap.eta.slice(11, 16) : '&mdash;') + '</span></div>',
      '<div class="detail-row"><span class="detail-label">Left Dock</span><span class="detail-value">' + (snap.left_dock ? snap.left_dock.slice(11, 16) : '&mdash;') + '</span></div>',
      '<div class="detail-row"><span class="detail-label">Direction</span><span class="detail-value">' + (snap.departing_terminal || '?') + ' &rarr; ' + (snap.arriving_terminal || '?') + '</span></div>',
      optALine,
    '</div>',
  ].join('\n');
}

function renderChart(c, highlightIdx) {
  const snaps = c.snapshots;
  if (snaps.length < 2) return '';
  const actual = c.actual_delay;
  const vals = snaps.map(s => s.prediction);
  const currs = snaps.map(s => s.current_delay);
  const maxVal = Math.max(...vals, actual, ...currs, 1);
  const w = Math.max(snaps.length * 5, 500);

  let bars = '';
  snaps.forEach((s, i) => {
    const h = (s.prediction / maxVal) * 80;
    const x = (i / snaps.length) * 100;
    const cname = i === highlightIdx ? 'chart-bar' : (s.prediction_source === 'flat_propagation' ? 'chart-bar flat' : 'chart-bar');
    bars += '<div class="' + cname + '" style="left:' + x + '%;height:' + h + 'px;" title="T-' + Math.abs(s.minutes_before) + 'm: pred ' + s.prediction + 'm"></div>';
    const ch = (s.current_delay / maxVal) * 80;
    bars += '<div class="chart-bar current" style="left:' + x + '%;height:' + ch + 'px;opacity:0.3;" title="curr ' + s.current_delay + 'm"></div>';
  });

  const yPct = (actual / maxVal) * 80;
  return [
    '<h3>Prediction Over Time</h3>',
    '<div class="chart" style="overflow-x:auto;">',
      '<div style="position:relative;height:86px;min-width:' + w + 'px;">',
        '<div class="actual-line" style="bottom:' + yPct + 'px;"></div>',
        '<div class="actual-label" style="bottom:' + (yPct - 12) + 'px;">actual ' + actual + 'm</div>',
        bars,
      '</div>',
    '</div>',
    '<div style="font-size:10px;color:#555;margin-top:2px;">',
      '<span style="color:#e94560;">&#9608;</span> prediction <span style="color:#8888ff;">&#9608;</span> current delay <span style="color:#4ecca3;">&#9473;</span> actual',
    '</div>',
  ].join('\n');
}

function updateView(c) {
  const snap = c.snapshots[curSnap];
  document.getElementById('snap-counter').textContent = (curSnap + 1) + ' / ' + c.snapshots.length;
  document.getElementById('snapshot-display').innerHTML = renderSnapshotHTML(snap, c);
  document.getElementById('chart-container').innerHTML = renderChart(c, curSnap);
  updateMap(c, curSnap);
}

function errColor(err, actual) {
  const absErr = Math.abs(err);
  return absErr > 20 ? '#e94560' : (absErr > 5 ? '#f0a500' : '#4ecca3');
}

function updateMap(c, idx) {
  if (vesselMarker) map.removeLayer(vesselMarker);
  trackLines.forEach(l => map.removeLayer(l));
  terminalMarkers.forEach(m => map.removeLayer(m));
  trackLines = []; terminalMarkers = [];

  const snaps = c.snapshots;
  if (snaps.length === 0) return;

  for (let i = 0; i < snaps.length - 1; i++) {
    const a = snaps[i], b = snaps[i + 1];
    if (a.lat === null || b.lat === null) continue;
    const err = (a.prediction - c.actual_delay);
    const color = errColor(err, c.actual_delay);
    const seg = L.polyline([[a.lat, a.lon], [b.lat, b.lon]], {
      color, weight: 3, opacity: 0.5
    }).addTo(map);
    trackLines.push(seg);
  }

  Object.entries(DATA.terminals).forEach(([name, pos]) => {
    const m = L.circleMarker([pos.lat, pos.lon], {
      radius: 6, color: '#0f3460', fillColor: '#555', fillOpacity: 0.8, weight: 1
    }).addTo(map);
    m.bindTooltip(name);
    terminalMarkers.push(m);
  });

  const snap = snaps[idx];
  if (snap.lat !== null && snap.lon !== null) {
    const err = snap.prediction - c.actual_delay;
    const color = errColor(err, c.actual_delay);
    vesselMarker = L.circleMarker([snap.lat, snap.lon], {
      radius: 10, color: '#fff', fillColor: color, fillOpacity: 0.9, weight: 2
    }).addTo(map);
    vesselMarker.bindTooltip(c.vessel + ' T-' + Math.abs(snap.minutes_before) + 'min');
  }

  const coords = snaps.filter(s => s.lat !== null).map(s => [s.lat, s.lon]);
  if (coords.length > 0) map.fitBounds(coords, { padding: [60, 60], maxZoom: 12 });
}

init();
</script>
</body>
</html>"""


if __name__ == "__main__":
    main()
