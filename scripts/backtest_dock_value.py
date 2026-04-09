"""Experiment: Does the at-dock model add value over Option A persisted?

Compares two approaches for predicting next-sailing delay:
1. Option A persisted: en-route ETA-based prediction, frozen once vessel docks
2. Option A + dock model: en-route prediction transitions to dock model once docked

For selected sailings, shows how the prediction evolves over time.

Usage:
    uv run python -m scripts.backtest_dock_value
"""

import logging
import sqlite3
from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from backend.database import get_connection, init_db

logger = logging.getLogger(__name__)

ROUTES = ["sea-bi", "ed-king"]
CROSSING_TIME = {"sea-bi": 35, "ed-king": 25}
TA_P10 = {"sea-bi": 9.3, "ed-king": 14.8}
TA_P75 = {"sea-bi": 22.0, "ed-king": 26.0}

# At-dock model features (matching production at_dock_model.py)
DOCK_FEATURE_COLS = [
    "route_abbrev",
    "departing_terminal_id",
    "vessel_id",
    "day_of_week",
    "hour_of_day",
    "is_weekend",
    "minutes_until_scheduled_departure",
    "minutes_at_dock",
    "current_fullness",
    "incoming_vehicle_fullness",
    "current_vessel_delay_minutes",
]
DOCK_CAT_COLS = ["route_abbrev", "departing_terminal_id", "vessel_id", "day_of_week"]


# ---------------------------------------------------------------------------
# Option A prediction
# ---------------------------------------------------------------------------


def option_a_prediction(current_delay: float, eta, next_sched, route: str) -> float:
    """Conditional ceiling with >4 threshold."""
    p10 = TA_P10[route]
    p75 = TA_P75[route]
    eta_floor_t = eta + timedelta(minutes=p10)
    floor = max(0.0, (eta_floor_t - next_sched).total_seconds() / 60)
    if current_delay > 4:
        eta_ceil_t = eta + timedelta(minutes=p75)
        ceiling = max(0.0, (eta_ceil_t - next_sched).total_seconds() / 60)
        return max(floor, min(current_delay, ceiling))
    return max(current_delay, floor)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_timeline_data(conn: sqlite3.Connection) -> dict:
    """Load all data needed for timeline analysis."""

    # --- Sailing events ---
    events = pd.read_sql_query(
        """
        SELECT id as event_id, vessel_id, vessel_name, route_abbrev,
               departing_terminal_id, arriving_terminal_id,
               scheduled_departure, actual_departure, delay_minutes,
               day_of_week, hour_of_day
        FROM sailing_events
        WHERE route_abbrev IN ('sea-bi', 'ed-king')
          AND arriving_terminal_id IS NOT NULL
        ORDER BY scheduled_departure
        """,
        conn,
    )
    for col in ["actual_departure", "scheduled_departure"]:
        events[col] = pd.to_datetime(events[col], format="ISO8601", utc=True)
    events["arriving_terminal_id"] = events["arriving_terminal_id"].astype("Int64")
    events["is_weekend"] = events["day_of_week"].isin([5, 6]).astype(int)

    # --- All vessel snapshots (en-route + at-dock) ---
    snapshots = pd.read_sql_query(
        """
        SELECT vessel_id, collected_at, at_dock, eta, scheduled_departure,
               speed, departing_terminal_id, route_abbrev
        FROM vessel_snapshots
        WHERE route_abbrev IN ('sea-bi', 'ed-king')
          AND scheduled_departure IS NOT NULL
        ORDER BY vessel_id, collected_at
        """,
        conn,
    )
    for col in ["collected_at", "scheduled_departure"]:
        snapshots[col] = pd.to_datetime(snapshots[col], format="ISO8601", utc=True)
    snapshots["eta"] = pd.to_datetime(snapshots["eta"], format="ISO8601", utc=True)

    # --- Space snapshots for fullness ---
    space = pd.read_sql_query(
        """
        SELECT departing_terminal_id, arriving_terminal_id, departure_time,
               collected_at, max_space_count, drive_up_space_count
        FROM sailing_space_snapshots
        WHERE max_space_count > 0
        """,
        conn,
    )
    space["collected_at_dt"] = pd.to_datetime(
        space["collected_at"], format="ISO8601", utc=True
    )
    space["departure_time_dt"] = pd.to_datetime(
        space["departure_time"], format="ISO8601", utc=True
    )
    space["fullness"] = 1.0 - space["drive_up_space_count"] / space["max_space_count"]

    return {"events": events, "snapshots": snapshots, "space": space}


def build_next_sailing_pairs(events: pd.DataFrame) -> pd.DataFrame:
    """Build pairs of consecutive sailings for the same vessel."""
    events_sorted = events.sort_values(["vessel_id", "scheduled_departure"])
    rows = []
    for _vid, grp in events_sorted.groupby("vessel_id"):
        grp = grp.reset_index(drop=True)
        for i in range(len(grp) - 1):
            curr = grp.loc[i]
            nxt = grp.loc[i + 1]
            gap_sched = (
                nxt["scheduled_departure"] - curr["scheduled_departure"]
            ).total_seconds() / 60
            # Only consecutive sailings with reasonable gap
            if gap_sched < 30 or gap_sched > 120:
                continue
            rows.append(
                {
                    "curr_event_id": curr["event_id"],
                    "curr_vessel_id": curr["vessel_id"],
                    "curr_vessel_name": curr["vessel_name"],
                    "curr_route": curr["route_abbrev"],
                    "curr_sched_dep": curr["scheduled_departure"],
                    "curr_actual_dep": curr["actual_departure"],
                    "curr_delay": float(curr["delay_minutes"]),
                    "curr_departing_terminal": curr["departing_terminal_id"],
                    "curr_arriving_terminal": curr["arriving_terminal_id"],
                    "curr_day_of_week": curr["day_of_week"],
                    "curr_hour_of_day": curr["hour_of_day"],
                    "curr_is_weekend": curr["is_weekend"],
                    "next_event_id": nxt["event_id"],
                    "next_sched_dep": nxt["scheduled_departure"],
                    "next_actual_dep": nxt["actual_departure"],
                    "next_delay": float(nxt["delay_minutes"]),
                    "next_departing_terminal": nxt["departing_terminal_id"],
                }
            )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Build dock model training data + train
# ---------------------------------------------------------------------------


def train_dock_model(
    events: pd.DataFrame, snapshots: pd.DataFrame, space: pd.DataFrame
) -> dict:
    """Train a simplified dock model matching production architecture."""
    # Get at-dock snapshots matched to sailing events
    dock_snaps = snapshots[snapshots["at_dock"] == 1].copy()
    dock_snaps = dock_snaps.merge(
        events[
            [
                "event_id",
                "vessel_id",
                "scheduled_departure",
                "delay_minutes",
                "route_abbrev",
                "departing_terminal_id",
                "day_of_week",
                "hour_of_day",
                "is_weekend",
            ]
        ],
        on=["vessel_id", "scheduled_departure"],
        how="inner",
        suffixes=("_snap", ""),
    )

    # minutes_at_dock: time since first dock snapshot for this sailing
    first_dock = (
        dock_snaps.groupby(["vessel_id", "scheduled_departure"])["collected_at"]
        .min()
        .reset_index()
        .rename(columns={"collected_at": "first_docked_at"})
    )
    dock_snaps = dock_snaps.merge(
        first_dock, on=["vessel_id", "scheduled_departure"], how="left"
    )
    dock_snaps["minutes_at_dock"] = (
        (dock_snaps["collected_at"] - dock_snaps["first_docked_at"]).dt.total_seconds()
        / 60
    ).clip(lower=0)

    # minutes_until_scheduled_departure
    dock_snaps["minutes_until_scheduled_departure"] = (
        (
            dock_snaps["scheduled_departure"] - dock_snaps["collected_at"]
        ).dt.total_seconds()
        / 60
    ).clip(lower=0)

    # Only keep pre-departure snapshots
    dock_snaps = dock_snaps[dock_snaps["minutes_until_scheduled_departure"] >= 0].copy()

    # current_fullness: merge_asof from space snapshots
    dock_snaps["current_fullness"] = np.nan
    for term_id in dock_snaps["departing_terminal_id"].unique():
        d_mask = dock_snaps["departing_terminal_id"] == term_id
        d_rows = dock_snaps.loc[d_mask].sort_values("collected_at")
        s_rows = space.loc[space["departing_terminal_id"] == term_id].sort_values(
            "collected_at_dt"
        )
        if s_rows.empty or d_rows.empty:
            continue
        matched = pd.merge_asof(
            d_rows[["event_id", "collected_at"]].rename(
                columns={"collected_at": "merge_key"}
            ),
            s_rows[["collected_at_dt", "fullness"]].rename(
                columns={"collected_at_dt": "merge_key", "fullness": "cf"}
            ),
            on="merge_key",
            direction="backward",
        )
        for idx, row in matched.iterrows():
            if pd.notna(row["cf"]):
                dock_snaps.loc[idx, "current_fullness"] = row["cf"]

    # incoming_vehicle_fullness: last snapshot of most recent inbound sailing
    inbound_last = (
        space.sort_values("collected_at_dt")
        .groupby(["arriving_terminal_id", "departure_time"])
        .last()
        .reset_index()
    )
    dock_snaps["incoming_vehicle_fullness"] = np.nan
    for term_id in dock_snaps["departing_terminal_id"].unique():
        d_mask = dock_snaps["departing_terminal_id"] == term_id
        d_rows = dock_snaps.loc[d_mask].sort_values("collected_at")
        i_rows = inbound_last.loc[
            inbound_last["arriving_terminal_id"] == term_id
        ].sort_values("departure_time_dt")
        if i_rows.empty or d_rows.empty:
            continue
        matched = pd.merge_asof(
            d_rows[["event_id", "collected_at"]].rename(
                columns={"collected_at": "merge_key"}
            ),
            i_rows[["departure_time_dt", "fullness"]].rename(
                columns={"departure_time_dt": "merge_key", "fullness": "ivf"}
            ),
            on="merge_key",
            direction="backward",
        )
        for idx, row in matched.iterrows():
            if pd.notna(row["ivf"]):
                dock_snaps.loc[idx, "incoming_vehicle_fullness"] = row["ivf"]

    # current_vessel_delay_minutes: use the current sailing's delay
    dock_snaps["current_vessel_delay_minutes"] = dock_snaps["delay_minutes"]

    # Target: actual delay
    dock_snaps["target"] = dock_snaps["delay_minutes"]

    logger.info(f"Dock model training data: {len(dock_snaps)} snapshots")

    # Encode categoricals
    cat_encoders = {}
    for col in DOCK_CAT_COLS:
        cats = dock_snaps[col].astype(str).unique()
        cat_encoders[col] = {v: i for i, v in enumerate(cats)}
        dock_snaps[col + "_enc"] = (
            dock_snaps[col].astype(str).map(cat_encoders[col]).fillna(-1).astype(int)
        )

    feature_cols_enc = [
        c + "_enc" if c in DOCK_CAT_COLS else c for c in DOCK_FEATURE_COLS
    ]
    X = dock_snaps[feature_cols_enc].values
    y = dock_snaps["target"].values

    # Train quantile models (matching production)
    models = {}
    for name, q in [("q50", 0.333), ("q10", 0.10), ("q90", 0.90)]:
        m = HistGradientBoostingRegressor(
            loss="quantile",
            quantile=q,
            max_iter=200,
            max_depth=5,
            learning_rate=0.1,
            min_samples_leaf=20,
            random_state=42,
        )
        m.fit(X, y)
        models[name] = m
        pred = m.predict(X)
        mae = np.abs(y - pred).mean()
        logger.info(f"  Dock model {name}: MAE={mae:.2f}")

    return {
        "models": models,
        "cat_encoders": cat_encoders,
        "dock_snaps": dock_snaps,
        "feature_cols_enc": feature_cols_enc,
    }


def predict_dock(
    row: dict,
    dock_models: dict,
) -> dict:
    """Predict using dock model."""
    cat_encoders = dock_models["cat_encoders"]
    features = []
    for col in DOCK_FEATURE_COLS:
        if col in DOCK_CAT_COLS:
            val = cat_encoders[col].get(str(row[col]), -1)
        else:
            val = row.get(col, np.nan)
            if val is None:
                val = np.nan
        features.append(val)

    X = np.array([features])
    return {
        "predicted_delay": float(dock_models["models"]["q50"].predict(X)[0]),
        "lower_bound": float(dock_models["models"]["q10"].predict(X)[0]),
        "upper_bound": float(dock_models["models"]["q90"].predict(X)[0]),
    }


# ---------------------------------------------------------------------------
# Timeline builder
# ---------------------------------------------------------------------------


def build_sailing_timeline(
    pair: pd.Series,
    snapshots: pd.DataFrame,
    space: pd.DataFrame,
    dock_models: dict,
) -> pd.DataFrame:
    """Build prediction timeline for a single next-sailing pair.

    Returns a DataFrame with one row per snapshot, showing how predictions
    evolve from en-route through docking to departure.
    """
    vessel_id = pair["curr_vessel_id"]
    sched_dep = pair["curr_sched_dep"]
    next_sched = pair["next_sched_dep"]
    route = pair["curr_route"]

    # Get all snapshots for this sailing (from departure to next departure)
    mask = (
        (snapshots["vessel_id"] == vessel_id)
        & (snapshots["scheduled_departure"] == sched_dep)
        & (snapshots["collected_at"] >= pair["curr_actual_dep"] - timedelta(minutes=5))
        & (snapshots["collected_at"] <= pair["next_actual_dep"] + timedelta(minutes=5))
    )
    sail_snaps = snapshots[mask].sort_values("collected_at").copy()
    if sail_snaps.empty:
        return pd.DataFrame()

    # Also get dock snapshots for the NEXT sailing (at the turnaround terminal)
    next_mask = (
        (snapshots["vessel_id"] == vessel_id)
        & (snapshots["scheduled_departure"] == next_sched)
        & (snapshots["at_dock"] == 1)
        & (snapshots["collected_at"] <= pair["next_actual_dep"] + timedelta(minutes=5))
    )
    next_dock_snaps = snapshots[next_mask].sort_values("collected_at")

    # Combine: en-route snaps from current sailing + dock snaps for next sailing
    timeline_rows = []

    # Phase 1: En-route snapshots
    enroute_snaps = sail_snaps[sail_snaps["at_dock"] == 0]
    last_option_a = None
    for _, snap in enroute_snaps.iterrows():
        eta = snap["eta"]
        if pd.isna(eta):
            continue

        # Sanity filter
        eta_mins = (eta - snap["collected_at"]).total_seconds() / 60
        max_reasonable = CROSSING_TIME.get(route, 35) * 2.0
        if eta_mins <= 0 or eta_mins > max_reasonable:
            continue

        pred = option_a_prediction(pair["curr_delay"], eta, next_sched, route)
        last_option_a = pred

        mins_into_crossing = (
            snap["collected_at"] - pair["curr_actual_dep"]
        ).total_seconds() / 60

        timeline_rows.append(
            {
                "collected_at": snap["collected_at"],
                "phase": "en-route",
                "mins_into_crossing": round(mins_into_crossing, 1),
                "option_a_pred": round(pred, 1),
                "dock_model_pred": None,
                "dock_model_lower": None,
                "dock_model_upper": None,
                "eta": eta,
            }
        )

    # Phase 2: At-dock snapshots for the NEXT sailing
    if not next_dock_snaps.empty:
        first_dock_time = next_dock_snaps.iloc[0]["collected_at"]

        # Get fullness data for the turnaround terminal
        turnaround_terminal = pair["curr_arriving_terminal"]

        # Inbound fullness (last snapshot of inbound sailing)
        inbound = space[space["arriving_terminal_id"] == turnaround_terminal]
        if not inbound.empty:
            inbound_last = (
                inbound.sort_values("collected_at_dt")
                .groupby("departure_time")
                .last()
                .reset_index()
            )
        else:
            inbound_last = pd.DataFrame()

        for _, snap in next_dock_snaps.iterrows():
            mins_at_dock = max(
                0, (snap["collected_at"] - first_dock_time).total_seconds() / 60
            )
            mins_until_sched = max(
                0, (next_sched - snap["collected_at"]).total_seconds() / 60
            )

            # Current fullness at turnaround terminal
            outbound = space[
                space["departing_terminal_id"] == turnaround_terminal
            ].sort_values("collected_at_dt")
            cf = np.nan
            if not outbound.empty:
                before = outbound[outbound["collected_at_dt"] <= snap["collected_at"]]
                if not before.empty:
                    cf = before.iloc[-1]["fullness"]

            # Incoming vehicle fullness
            ivf = np.nan
            if not inbound_last.empty:
                before = inbound_last[
                    inbound_last["departure_time_dt"] <= snap["collected_at"]
                ]
                if not before.empty:
                    ivf = before.iloc[-1]["fullness"]

            dock_features = {
                "route_abbrev": pair["curr_route"],
                "departing_terminal_id": int(turnaround_terminal),
                "vessel_id": vessel_id,
                "day_of_week": pair["curr_day_of_week"],
                "hour_of_day": pair["curr_hour_of_day"],
                "is_weekend": pair["curr_is_weekend"],
                "minutes_until_scheduled_departure": mins_until_sched,
                "minutes_at_dock": mins_at_dock,
                "current_fullness": cf,
                "incoming_vehicle_fullness": ivf,
                "current_vessel_delay_minutes": pair["curr_delay"],
            }

            dock_pred = predict_dock(dock_features, dock_models)

            mins_since_departure = (
                snap["collected_at"] - pair["curr_actual_dep"]
            ).total_seconds() / 60

            timeline_rows.append(
                {
                    "collected_at": snap["collected_at"],
                    "phase": "at-dock",
                    "mins_into_crossing": round(mins_since_departure, 1),
                    "option_a_pred": last_option_a,  # persisted
                    "dock_model_pred": round(dock_pred["predicted_delay"], 1),
                    "dock_model_lower": round(dock_pred["lower_bound"], 1),
                    "dock_model_upper": round(dock_pred["upper_bound"], 1),
                    "eta": None,
                }
            )

    return pd.DataFrame(timeline_rows)


# ---------------------------------------------------------------------------
# Aggregate evaluation
# ---------------------------------------------------------------------------


def evaluate_all_pairs(
    pairs: pd.DataFrame,
    snapshots: pd.DataFrame,
    space: pd.DataFrame,
    dock_models: dict,
) -> pd.DataFrame:
    """Vectorized: for each pair, get last en-route and last at-dock predictions."""
    logger.info("  Pre-computing last en-route ETAs...")

    # --- Step 1: Last valid en-route ETA per (vessel_id, scheduled_departure) ---
    enroute = snapshots[(snapshots["at_dock"] == 0) & (snapshots["eta"].notna())].copy()
    enroute["eta_mins"] = (
        enroute["eta"] - enroute["collected_at"]
    ).dt.total_seconds() / 60
    # Build route lookup for max crossing time filter
    route_max = enroute["route_abbrev"].map(lambda r: CROSSING_TIME.get(r, 35) * 2.0)
    enroute = enroute[(enroute["eta_mins"] > 0) & (enroute["eta_mins"] <= route_max)]
    # Keep last per sailing
    last_enroute = (
        enroute.sort_values("collected_at")
        .groupby(["vessel_id", "scheduled_departure"])
        .last()
        .reset_index()
    )[["vessel_id", "scheduled_departure", "eta", "collected_at", "route_abbrev"]]
    last_enroute = last_enroute.rename(
        columns={"eta": "last_eta", "collected_at": "last_enroute_at"}
    )

    # --- Step 2: Merge last ETA onto pairs ---
    merged = pairs.merge(
        last_enroute,
        left_on=["curr_vessel_id", "curr_sched_dep"],
        right_on=["vessel_id", "scheduled_departure"],
        how="left",
    ).drop(columns=["vessel_id", "scheduled_departure", "route_abbrev"])
    # Drop pairs without en-route ETA
    merged = merged[merged["last_eta"].notna()].copy()
    logger.info(f"  Pairs with en-route ETA: {len(merged)}")

    # --- Step 3: Compute Option A predictions vectorized ---
    opt_a_preds = []
    for _, row in merged.iterrows():
        opt_a_preds.append(
            option_a_prediction(
                row["curr_delay"],
                row["last_eta"],
                row["next_sched_dep"],
                row["curr_route"],
            )
        )
    merged["option_a"] = opt_a_preds

    # --- Step 4: Pre-compute dock features in bulk ---
    logger.info("  Pre-computing dock model features...")
    # First/last dock snapshot per (vessel_id, scheduled_departure) for next sailing
    dock_snaps = snapshots[snapshots["at_dock"] == 1].copy()
    dock_agg = (
        dock_snaps.groupby(["vessel_id", "scheduled_departure"])
        .agg(
            first_dock_at=("collected_at", "min"),
            last_dock_at=("collected_at", "max"),
        )
        .reset_index()
    )

    merged = merged.merge(
        dock_agg,
        left_on=["curr_vessel_id", "next_sched_dep"],
        right_on=["vessel_id", "scheduled_departure"],
        how="left",
    ).drop(columns=["vessel_id", "scheduled_departure"])

    has_dock = merged["last_dock_at"].notna()
    # Filter to pre-departure dock snapshots
    has_dock = has_dock & (merged["last_dock_at"] <= merged["next_actual_dep"])
    dock_rows = merged[has_dock].copy()

    dock_rows["minutes_at_dock"] = (
        (dock_rows["last_dock_at"] - dock_rows["first_dock_at"]).dt.total_seconds() / 60
    ).clip(lower=0)
    dock_rows["minutes_until_scheduled_departure"] = (
        (dock_rows["next_sched_dep"] - dock_rows["last_dock_at"]).dt.total_seconds()
        / 60
    ).clip(lower=0)

    # --- Step 5: Fullness lookups via merge_asof ---
    logger.info("  Computing fullness features...")
    # Pre-compute per-terminal sorted space for outbound fullness
    space_sorted = space.sort_values("collected_at_dt")
    # Pre-compute inbound last snapshot
    inbound_last = (
        space_sorted.groupby(["arriving_terminal_id", "departure_time"])
        .last()
        .reset_index()
        .sort_values("departure_time_dt")
    )

    # Outbound fullness: merge_asof per turnaround terminal
    dock_rows["current_fullness"] = np.nan
    dock_rows["incoming_vehicle_fullness"] = np.nan
    for term_id in dock_rows["curr_arriving_terminal"].unique():
        tmask = dock_rows["curr_arriving_terminal"] == term_id
        d = dock_rows.loc[tmask].sort_values("last_dock_at")
        if d.empty:
            continue

        # Outbound (departing from turnaround terminal)
        s_out = space_sorted[space_sorted["departing_terminal_id"] == term_id]
        if not s_out.empty:
            matched = pd.merge_asof(
                d[["last_dock_at"]].rename(columns={"last_dock_at": "t"}),
                s_out[["collected_at_dt", "fullness"]].rename(
                    columns={"collected_at_dt": "t"}
                ),
                on="t",
                direction="backward",
            )
            dock_rows.loc[tmask, "current_fullness"] = matched["fullness"].values

        # Inbound (arriving at turnaround terminal)
        i_in = inbound_last[inbound_last["arriving_terminal_id"] == term_id]
        if not i_in.empty:
            matched = pd.merge_asof(
                d[["last_dock_at"]].rename(columns={"last_dock_at": "t"}),
                i_in[["departure_time_dt", "fullness"]].rename(
                    columns={"departure_time_dt": "t"}
                ),
                on="t",
                direction="backward",
            )
            dock_rows.loc[tmask, "incoming_vehicle_fullness"] = matched[
                "fullness"
            ].values

    # --- Step 6: Batch dock model prediction ---
    logger.info("  Running dock model predictions...")
    cat_encoders = dock_models["cat_encoders"]
    feature_rows = []
    for _, row in dock_rows.iterrows():
        features = []
        for col in DOCK_FEATURE_COLS:
            if col == "route_abbrev":
                features.append(cat_encoders[col].get(str(row["curr_route"]), -1))
            elif col == "departing_terminal_id":
                features.append(
                    cat_encoders[col].get(str(int(row["curr_arriving_terminal"])), -1)
                )
            elif col == "vessel_id":
                features.append(cat_encoders[col].get(str(row["curr_vessel_id"]), -1))
            elif col == "day_of_week":
                features.append(cat_encoders[col].get(str(row["curr_day_of_week"]), -1))
            elif col in DOCK_CAT_COLS:
                features.append(cat_encoders[col].get(str(row.get(col, "")), -1))
            elif col == "hour_of_day":
                features.append(row["curr_hour_of_day"])
            elif col == "is_weekend":
                features.append(row["curr_is_weekend"])
            elif col == "current_vessel_delay_minutes":
                features.append(row["curr_delay"])
            else:
                features.append(row.get(col, np.nan))
        feature_rows.append(features)

    if feature_rows:
        X_dock = np.array(feature_rows)
        dock_preds = dock_models["models"]["q50"].predict(X_dock)
        dock_rows["dock_pred"] = dock_preds
    else:
        dock_rows["dock_pred"] = np.nan

    # --- Step 7: Assemble results ---
    merged["dock_pred"] = np.nan
    merged.loc[dock_rows.index, "dock_pred"] = dock_rows["dock_pred"].values

    merged["option_a_err"] = merged["option_a"] - merged["next_delay"]
    merged["dock_err"] = merged["dock_pred"] - merged["next_delay"]

    return merged[
        [
            "curr_event_id",
            "curr_route",
            "curr_vessel_name",
            "curr_delay",
            "next_delay",
            "option_a",
            "dock_pred",
            "option_a_err",
            "dock_err",
        ]
    ].rename(
        columns={
            "curr_event_id": "event_id",
            "curr_route": "route",
            "curr_vessel_name": "vessel_name",
        }
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    from zoneinfo import ZoneInfo

    PAC = ZoneInfo("America/Los_Angeles")
    init_db()
    conn = get_connection()
    data = load_timeline_data(conn)

    events = data["events"]
    snapshots = data["snapshots"]
    space = data["space"]

    logger.info("Training dock model...")
    dock_models = train_dock_model(events, snapshots, space)

    logger.info("Building next-sailing pairs...")
    pairs = build_next_sailing_pairs(events)
    logger.info(f"Built {len(pairs)} pairs")

    # --- Aggregate evaluation ---
    logger.info("Running aggregate evaluation...")
    results = evaluate_all_pairs(pairs, snapshots, space, dock_models)
    logger.info(f"Evaluated {len(results)} pairs")

    has_dock = results["dock_pred"].notna()
    both = results[has_dock].copy()

    opt_a_mae = both["option_a_err"].abs().mean()
    dock_mae = both["dock_err"].abs().mean()
    print("\n" + "=" * 70)
    print("AGGREGATE: Option A persisted vs Option A + dock model")
    print(f"Pairs with dock predictions: {len(both)}/{len(results)}")
    print("=" * 70)
    print(
        f"  Option A persisted:   MAE={opt_a_mae:.2f}  "
        f"bias={both['option_a_err'].mean():+.2f}"
    )
    print(
        f"  Dock model (last):    MAE={dock_mae:.2f}  "
        f"bias={both['dock_err'].mean():+.2f}"
    )

    # By delay bucket
    print("\nBy delay bucket:")
    for name, lo, hi in [
        ("on_time", -999, 1),
        ("minor", 1, 5),
        ("moderate", 5, 15),
        ("major", 15, 999),
    ]:
        mask = (both["next_delay"] >= lo) & (both["next_delay"] < hi)
        if mask.sum() < 5:
            continue
        sub = both[mask]
        print(
            f"  {name:10s} (n={len(sub):5d}): "
            f"OptA MAE={sub['option_a_err'].abs().mean():.2f}  "
            f"Dock MAE={sub['dock_err'].abs().mean():.2f}  "
            f"Δ={sub['option_a_err'].abs().mean() - sub['dock_err'].abs().mean():+.2f}"
        )

    # By route
    print("\nBy route:")
    for route in ROUTES:
        sub = both[both["route"] == route]
        if sub.empty:
            continue
        print(
            f"  {route:10s} (n={len(sub):5d}): "
            f"OptA MAE={sub['option_a_err'].abs().mean():.2f}  "
            f"Dock MAE={sub['dock_err'].abs().mean():.2f}  "
            f"Δ={sub['option_a_err'].abs().mean() - sub['dock_err'].abs().mean():+.2f}"
        )

    # Win/loss
    opt_a_wins = (both["option_a_err"].abs() < both["dock_err"].abs()).sum()
    dock_wins = (both["dock_err"].abs() < both["option_a_err"].abs()).sum()
    ties = len(both) - opt_a_wins - dock_wins
    print(
        f"\nHead-to-head: Option A wins {opt_a_wins}, "
        f"Dock wins {dock_wins}, ties {ties}"
    )

    # --- Timeline examples ---
    print("\n" + "=" * 70)
    print("TIMELINE EXAMPLES")
    print("=" * 70)

    def fmt(ts):
        if pd.isna(ts):
            return "N/A"
        return ts.astimezone(PAC).strftime("%I:%M %p")

    # Pick interesting examples
    scenarios = []

    # Howler case: Option A floor fires, flat would be wrong
    howler_mask = (both["curr_delay"] < 5) & (both["next_delay"] > 15)
    if howler_mask.sum() > 0:
        scenarios.append(("Howler: small delay → big next delay", howler_mask))

    # Recovery: big delay → on time
    recovery_mask = (both["curr_delay"] > 15) & (both["next_delay"] < 3)
    if recovery_mask.sum() > 0:
        scenarios.append(("Recovery: big delay → on time", recovery_mask))

    # Persistent delay
    persist_mask = (both["curr_delay"] > 10) & (both["next_delay"] > 10)
    if persist_mask.sum() > 0:
        scenarios.append(("Persistent: delay carries forward", persist_mask))

    # Dock model significantly better
    dock_better_mask = (
        both["dock_err"].abs() < both["option_a_err"].abs() - 3
    ) & has_dock
    if dock_better_mask.sum() > 0:
        scenarios.append(("Dock model significantly better", dock_better_mask))

    # Option A significantly better
    opt_a_better_mask = (
        both["option_a_err"].abs() < both["dock_err"].abs() - 3
    ) & has_dock
    if opt_a_better_mask.sum() > 0:
        scenarios.append(("Option A significantly better", opt_a_better_mask))

    for scenario_name, mask in scenarios:
        row = both[mask].iloc[0]
        pair = pairs[pairs["curr_event_id"] == row["event_id"]].iloc[0]

        print(f"\n### {scenario_name}")
        print(
            f"**{pair['curr_vessel_name']}** on **{pair['curr_route']}** "
            f"— {fmt(pair['curr_actual_dep'])}"
        )
        print(f"  Current delay: {pair['curr_delay']:.1f} min")
        print(f"  Next sched:    {fmt(pair['next_sched_dep'])}")
        print(f"  Next actual:   {fmt(pair['next_actual_dep'])}")
        print(f"  Next delay:    {pair['next_delay']:.1f} min")
        print()

        timeline = build_sailing_timeline(pair, snapshots, space, dock_models)
        if timeline.empty:
            print("  (no timeline data)")
            continue

        print(
            f"  {'Time':>10s}  {'Phase':>10s}  {'Option A':>10s}  "
            f"{'Dock Model':>12s}  {'Actual':>8s}"
        )
        print(f"  {'-' * 10}  {'-' * 10}  {'-' * 10}  {'-' * 12}  {'-' * 8}")

        # Sample ~10 snapshots evenly
        if len(timeline) > 12:
            indices = np.linspace(0, len(timeline) - 1, 12, dtype=int)
            timeline_sample = timeline.iloc[indices]
        else:
            timeline_sample = timeline

        for _, t in timeline_sample.iterrows():
            time_str = fmt(t["collected_at"])
            phase = t["phase"]
            opt_a_str = (
                f"{t['option_a_pred']:.1f}" if t["option_a_pred"] is not None else "—"
            )
            if t["dock_model_pred"] is not None:
                dock_str = (
                    f"{t['dock_model_pred']:.1f} "
                    f"[{t['dock_model_lower']:.0f}–{t['dock_model_upper']:.0f}]"
                )
            else:
                dock_str = "—"
            print(
                f"  {time_str:>10s}  {phase:>10s}  {opt_a_str:>10s}  "
                f"{dock_str:>12s}  {pair['next_delay']:>7.1f}"
            )

        print(
            f"\n  Final: Option A={row['option_a']:.1f} (err {row['option_a_err']:+.1f}), "
            f"Dock={row['dock_pred']:.1f} (err {row['dock_err']:+.1f}), "
            f"Actual={row['next_delay']:.1f}"
        )


if __name__ == "__main__":
    main()
