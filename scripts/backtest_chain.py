"""Experiment 35: Does the en-route GBT model add value beyond Option A + flat propagation?

Builds chains of 3+ consecutive sailings per vessel and compares prediction
approaches at each hop:

  sailing[0] = "next sailing" (the one users care about most)
  sailing[1] = 2 sailings out (~60-90 min)
  sailing[2] = 3 sailings out (~120+ min)

Approaches compared:
  1. Flat propagation: copy current delay to all future sailings
  2. Option A + flat: Option A for [0], copy that prediction to [1], [2]
  3. Flat + GBT: flat for [0], GBT model for [1], [2]
  4. Option A + GBT: Option A for [0], GBT for [1], [2]

Usage:
    uv run python -m scripts.backtest_chain
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
P10_TA = {"sea-bi": 9.3, "ed-king": 14.8}
P75_TA = {"sea-bi": 22.0, "ed-king": 26.0}
CEILING_THRESHOLD = 4  # minutes


# ---------------------------------------------------------------------------
# Option A prediction (same as production)
# ---------------------------------------------------------------------------


def predict_option_a(current_delay: float, eta, next_sched, route: str) -> float:
    """Conditional ceiling with >4 threshold."""
    p10 = P10_TA.get(route)
    p75 = P75_TA.get(route)
    if p10 is None or p75 is None:
        return current_delay

    eta_floor_t = eta + timedelta(minutes=p10)
    floor = max(0.0, (eta_floor_t - next_sched).total_seconds() / 60)

    if current_delay > CEILING_THRESHOLD:
        eta_ceil_t = eta + timedelta(minutes=p75)
        ceiling = max(0.0, (eta_ceil_t - next_sched).total_seconds() / 60)
        return max(floor, min(current_delay, ceiling))
    return max(current_delay, floor)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_data(conn: sqlite3.Connection) -> dict:
    """Load sailing events with derived arrivals."""
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
    logger.info(f"Loaded {len(events)} sailing events")

    # Derive actual arrivals via merge_asof on dock snapshots
    dock_df = pd.read_sql_query(
        """
        SELECT vessel_id, collected_at,
               departing_terminal_id as arriving_terminal_id
        FROM vessel_snapshots WHERE at_dock = 1
        ORDER BY vessel_id, collected_at
        """,
        conn,
    )
    dock_df["collected_at"] = pd.to_datetime(
        dock_df["collected_at"], format="ISO8601", utc=True
    )
    dock_df["arriving_terminal_id"] = dock_df["arriving_terminal_id"].astype("Int64")

    dock_groups = dock_df.groupby(["vessel_id", "arriving_terminal_id"])
    arrival_parts = []
    for key, ev_group in events.groupby(["vessel_id", "arriving_terminal_id"]):
        ev_sorted = ev_group.sort_values("actual_departure")
        if key not in dock_groups.groups:
            ev_sorted = ev_sorted.copy()
            ev_sorted["actual_arrival"] = pd.NaT
            arrival_parts.append(ev_sorted)
            continue
        dk = (
            dock_df.loc[dock_groups.groups[key]]
            .sort_values("collected_at")[["collected_at"]]
            .rename(columns={"collected_at": "actual_arrival"})
        )
        arrival_parts.append(
            pd.merge_asof(
                ev_sorted,
                dk,
                left_on="actual_departure",
                right_on="actual_arrival",
                direction="forward",
                tolerance=pd.Timedelta(minutes=90),
            )
        )
    events = pd.concat(arrival_parts, ignore_index=True).sort_values(
        "scheduled_departure"
    )

    # En-route snapshots with ETA (for Option A)
    enroute = pd.read_sql_query(
        """
        SELECT vessel_id, collected_at, eta, scheduled_departure, speed
        FROM vessel_snapshots
        WHERE at_dock = 0 AND eta IS NOT NULL AND eta != ''
          AND route_abbrev IN ('sea-bi', 'ed-king')
        ORDER BY vessel_id, collected_at
        """,
        conn,
    )
    for col in ["collected_at", "scheduled_departure"]:
        enroute[col] = pd.to_datetime(enroute[col], format="ISO8601", utc=True)
    enroute["eta"] = pd.to_datetime(enroute["eta"], format="ISO8601", utc=True)

    # Sanity filter ETAs
    enroute["eta_mins"] = (
        enroute["eta"] - enroute["collected_at"]
    ).dt.total_seconds() / 60
    route_max = enroute.merge(
        events[["vessel_id", "scheduled_departure", "route_abbrev"]],
        on=["vessel_id", "scheduled_departure"],
        how="left",
    )["route_abbrev"].map(lambda r: CROSSING_TIME.get(r, 35) * 2.0)
    enroute = enroute[(enroute["eta_mins"] > 0) & (enroute["eta_mins"] <= route_max)]

    # Last sane ETA per sailing
    last_eta = (
        enroute.sort_values("collected_at")
        .groupby(["vessel_id", "scheduled_departure"])
        .last()
        .reset_index()
    )[["vessel_id", "scheduled_departure", "eta"]]
    last_eta = last_eta.rename(columns={"eta": "last_eta"})

    return {"events": events, "last_eta": last_eta}


# ---------------------------------------------------------------------------
# Build sailing chains (3+ consecutive sailings per vessel)
# ---------------------------------------------------------------------------


def build_chains(events: pd.DataFrame, last_eta: pd.DataFrame) -> pd.DataFrame:
    """Build chains of 3 consecutive sailings per vessel.

    Returns one row per chain with columns for sailing[0], [1], [2].
    """
    ev = events.dropna(subset=["actual_arrival"]).sort_values(
        ["vessel_id", "scheduled_departure"]
    )

    # Merge last ETA onto each event
    ev = ev.merge(last_eta, on=["vessel_id", "scheduled_departure"], how="left")

    chains = []
    for _vid, grp in ev.groupby("vessel_id"):
        grp = grp.reset_index(drop=True)
        for i in range(len(grp) - 2):
            s0 = grp.loc[i]
            s1 = grp.loc[i + 1]
            s2 = grp.loc[i + 2]

            # Verify consecutive (reasonable gaps)
            gap_01 = (
                s1["actual_departure"] - s0["actual_arrival"]
            ).total_seconds() / 60
            gap_12 = (
                s2["actual_departure"] - s1["actual_arrival"]
            ).total_seconds() / 60
            if gap_01 < 5 or gap_01 > 60 or gap_12 < 5 or gap_12 > 60:
                continue

            # Need ETA for sailing[0] to compute Option A
            has_eta = pd.notna(s0["last_eta"])

            chains.append(
                {
                    # Sailing[0] — current crossing
                    "route": s0["route_abbrev"],
                    "vessel_id": s0["vessel_id"],
                    "vessel_name": s0["vessel_name"],
                    "s0_delay": float(s0["delay_minutes"]),
                    "s0_sched_dep": s0["scheduled_departure"],
                    "s0_actual_dep": s0["actual_departure"],
                    "s0_eta": s0["last_eta"] if has_eta else pd.NaT,
                    "s0_day_of_week": s0["day_of_week"],
                    "s0_hour_of_day": s0["hour_of_day"],
                    # Sailing[1] — next sailing (what Option A predicts)
                    "s1_sched_dep": s1["scheduled_departure"],
                    "s1_actual_dep": s1["actual_departure"],
                    "s1_delay": float(s1["delay_minutes"]),
                    "s1_day_of_week": s1["day_of_week"],
                    "s1_hour_of_day": s1["hour_of_day"],
                    # Sailing[2] — two sailings out
                    "s2_sched_dep": s2["scheduled_departure"],
                    "s2_actual_dep": s2["actual_departure"],
                    "s2_delay": float(s2["delay_minutes"]),
                    "s2_day_of_week": s2["day_of_week"],
                    "s2_hour_of_day": s2["hour_of_day"],
                    # Metadata
                    "has_eta": has_eta,
                }
            )

    df = pd.DataFrame(chains)
    logger.info(
        f"Built {len(df)} chains, {df['has_eta'].sum()} with ETA "
        f"({df['has_eta'].mean() * 100:.0f}%)"
    )
    return df


# ---------------------------------------------------------------------------
# Train en-route GBT model (matching production architecture)
# ---------------------------------------------------------------------------


def train_enroute_gbt(conn: sqlite3.Connection) -> dict:
    """Train HistGBT quantile model matching production ml_predictor.

    Features: route_abbrev, departing_terminal_id, day_of_week, hour_of_day,
    is_weekend, minutes_until_scheduled_departure, current_vessel_delay_minutes
    """
    logger.info("Training en-route GBT model...")

    events = pd.read_sql_query(
        """
        SELECT vessel_id, route_abbrev, departing_terminal_id,
               day_of_week, hour_of_day,
               scheduled_departure, actual_departure, delay_minutes
        FROM sailing_events
        WHERE route_abbrev IN ('sea-bi', 'ed-king')
        ORDER BY scheduled_departure
        """,
        conn,
    )
    events["scheduled_departure"] = pd.to_datetime(
        events["scheduled_departure"], format="ISO8601", utc=True
    )
    events["actual_departure"] = pd.to_datetime(
        events["actual_departure"], format="ISO8601", utc=True
    )
    events["is_weekend"] = events["day_of_week"].isin([5, 6]).astype(int)

    # Encode categoricals
    cat_cols = ["route_abbrev", "departing_terminal_id"]
    cat_encoders = {}
    for col in cat_cols:
        cats = events[col].astype(str).unique()
        cat_encoders[col] = {v: i for i, v in enumerate(cats)}
        events[col + "_enc"] = (
            events[col].astype(str).map(cat_encoders[col]).fillna(-1).astype(int)
        )

    # Expand by horizon: for each event, create rows at various horizons
    # mimicking what the production model sees (delay at N minutes before departure)
    horizons = [5, 10, 15, 20, 30, 45, 60, 90, 120]
    expanded = []
    for _, ev in events.iterrows():
        for h in horizons:
            expanded.append(
                {
                    "route_enc": ev["route_abbrev_enc"],
                    "terminal_enc": ev["departing_terminal_id_enc"],
                    "day_of_week": ev["day_of_week"],
                    "hour_of_day": ev["hour_of_day"],
                    "is_weekend": ev["is_weekend"],
                    "minutes_until_departure": h,
                    "current_delay": float(
                        ev["delay_minutes"]
                    ),  # simplified: use actual delay
                    "actual_delay": float(ev["delay_minutes"]),
                }
            )
    expanded_df = pd.DataFrame(expanded)

    feature_cols = [
        "route_enc",
        "terminal_enc",
        "day_of_week",
        "hour_of_day",
        "is_weekend",
        "minutes_until_departure",
        "current_delay",
    ]
    X = expanded_df[feature_cols].values
    y = expanded_df["actual_delay"].values

    # Train quantile model (q33 = production optimal)
    model = HistGradientBoostingRegressor(
        loss="quantile",
        quantile=0.333,
        max_iter=200,
        max_depth=6,
        learning_rate=0.1,
        min_samples_leaf=20,
        random_state=42,
    )
    model.fit(X, y)
    pred = model.predict(X)
    mae = np.abs(y - pred).mean()
    logger.info(f"En-route GBT trained: MAE={mae:.2f} on {len(expanded_df)} rows")

    return {
        "model": model,
        "cat_encoders": cat_encoders,
        "feature_cols": feature_cols,
    }


def predict_gbt(
    gbt: dict,
    route: str,
    terminal_id: int,
    day_of_week: int,
    hour_of_day: int,
    is_weekend: int,
    minutes_until: float,
    current_delay: float,
) -> float:
    """Predict delay using en-route GBT model."""
    route_enc = gbt["cat_encoders"]["route_abbrev"].get(route, -1)
    term_enc = gbt["cat_encoders"]["departing_terminal_id"].get(str(terminal_id), -1)
    X = np.array(
        [
            [
                route_enc,
                term_enc,
                day_of_week,
                hour_of_day,
                is_weekend,
                minutes_until,
                current_delay,
            ]
        ]
    )
    return float(gbt["model"].predict(X)[0])


# ---------------------------------------------------------------------------
# Evaluate chains
# ---------------------------------------------------------------------------


def evaluate_chains(chains: pd.DataFrame, gbt: dict) -> dict:
    """Evaluate all prediction approaches at each hop."""
    # Only chains with ETA (needed for Option A)
    with_eta = chains[chains["has_eta"]].copy()
    logger.info(f"Evaluating {len(with_eta)} chains with ETA")

    # --- Compute Option A predictions for sailing[0] ---
    opt_a_s0 = []
    for _, row in with_eta.iterrows():
        opt_a_s0.append(
            predict_option_a(
                row["s0_delay"], row["s0_eta"], row["s1_sched_dep"], row["route"]
            )
        )
    with_eta["opt_a_s0"] = opt_a_s0

    # --- Compute GBT predictions for sailing[1] and [2] ---
    gbt_from_flat_s1 = []
    gbt_from_flat_s2 = []
    gbt_from_opt_a_s1 = []
    gbt_from_opt_a_s2 = []

    for _, row in with_eta.iterrows():
        is_wknd = 1 if row["s0_day_of_week"] in [5, 6] else 0
        # We don't know the departing terminal for s1/s2 at prediction time,
        # but we know the vessel alternates. Use a reasonable approximation.
        # For the GBT, we feed current_delay and time horizon.

        # Time horizons (approximate)
        mins_to_s1 = max(
            5, (row["s1_sched_dep"] - row["s0_actual_dep"]).total_seconds() / 60
        )
        mins_to_s2 = max(
            5, (row["s2_sched_dep"] - row["s0_actual_dep"]).total_seconds() / 60
        )

        # GBT from flat delay (current production-like approach)
        gbt_from_flat_s1.append(
            predict_gbt(
                gbt,
                row["route"],
                0,
                row["s0_day_of_week"],
                row["s0_hour_of_day"],
                is_wknd,
                mins_to_s1,
                row["s0_delay"],
            )
        )
        gbt_from_flat_s2.append(
            predict_gbt(
                gbt,
                row["route"],
                0,
                row["s0_day_of_week"],
                row["s0_hour_of_day"],
                is_wknd,
                mins_to_s2,
                row["s0_delay"],
            )
        )

        # GBT from Option A prediction (Option A adjusts the delay fed to GBT)
        gbt_from_opt_a_s1.append(
            predict_gbt(
                gbt,
                row["route"],
                0,
                row["s1_day_of_week"],
                row["s1_hour_of_day"],
                is_wknd,
                mins_to_s1,
                row["opt_a_s0"],
            )
        )
        gbt_from_opt_a_s2.append(
            predict_gbt(
                gbt,
                row["route"],
                0,
                row["s2_day_of_week"],
                row["s2_hour_of_day"],
                is_wknd,
                mins_to_s2,
                row["opt_a_s0"],
            )
        )

    with_eta["gbt_flat_s1"] = gbt_from_flat_s1
    with_eta["gbt_flat_s2"] = gbt_from_flat_s2
    with_eta["gbt_opta_s1"] = gbt_from_opt_a_s1
    with_eta["gbt_opta_s2"] = gbt_from_opt_a_s2

    # The chain is: s0 (departs) → crosses → s1 (next departure) → crosses → s2
    # When s0 departs, we predict:
    #   hop 0 = s1 (the next sailing at opposite terminal) → target: s1_delay
    #   hop 1 = s2 (two sailings out) → target: s2_delay

    results = {}

    # --- Hop 0: Predict next sailing (s1_delay) ---
    hop0_target = with_eta["s1_delay"]
    results["hop0"] = {}
    for name, preds in [
        ("Flat propagation", with_eta["s0_delay"]),
        ("Option A", with_eta["opt_a_s0"]),
    ]:
        err = preds - hop0_target
        results["hop0"][name] = {
            "mae": round(float(err.abs().mean()), 2),
            "bias": round(float(err.mean()), 2),
            "within_3": round(float((err.abs() <= 3).mean() * 100), 1),
            "within_5": round(float((err.abs() <= 5).mean() * 100), 1),
        }

    # --- Hop 1: Predict sailing[1] = s2_delay ---
    hop1_target = with_eta["s2_delay"]
    results["hop1"] = {}
    for name, preds in [
        ("Flat propagation", with_eta["s0_delay"]),
        ("Option A + flat", with_eta["opt_a_s0"]),
        ("Flat + GBT", with_eta["gbt_flat_s2"]),
        ("Option A + GBT", with_eta["gbt_opta_s2"]),
    ]:
        err = preds - hop1_target
        results["hop1"][name] = {
            "mae": round(float(err.abs().mean()), 2),
            "bias": round(float(err.mean()), 2),
            "within_3": round(float((err.abs() <= 3).mean() * 100), 1),
            "within_5": round(float((err.abs() <= 5).mean() * 100), 1),
        }

    # --- By delay bucket for hop 1 ---
    results["hop1_buckets"] = {}
    for bkt_name, lo, hi in [
        ("on_time", -999, 1),
        ("minor", 1, 5),
        ("moderate", 5, 15),
        ("major", 15, 999),
    ]:
        mask = (hop1_target >= lo) & (hop1_target < hi)
        if mask.sum() < 10:
            continue
        bkt = {}
        for name, preds in [
            ("Flat propagation", with_eta["s0_delay"]),
            ("Option A + flat", with_eta["opt_a_s0"]),
            ("Flat + GBT", with_eta["gbt_flat_s2"]),
            ("Option A + GBT", with_eta["gbt_opta_s2"]),
        ]:
            err = preds[mask] - hop1_target[mask]
            bkt[name] = {"mae": round(float(err.abs().mean()), 2)}
        results["hop1_buckets"][bkt_name] = bkt

    # --- Time horizon analysis: how does accuracy degrade with distance? ---
    with_eta["mins_to_s1"] = (
        with_eta["s1_sched_dep"] - with_eta["s0_actual_dep"]
    ).dt.total_seconds() / 60
    with_eta["mins_to_s2"] = (
        with_eta["s2_sched_dep"] - with_eta["s0_actual_dep"]
    ).dt.total_seconds() / 60

    results["horizons"] = {
        "avg_mins_to_s1": round(float(with_eta["mins_to_s1"].mean()), 0),
        "avg_mins_to_s2": round(float(with_eta["mins_to_s2"].mean()), 0),
    }

    return results, with_eta


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    init_db()

    conn = get_connection()
    data = load_data(conn)
    chains = build_chains(data["events"], data["last_eta"])
    gbt = train_enroute_gbt(conn)
    conn.close()

    results, df = evaluate_chains(chains, gbt)

    # --- Print results ---
    print("\n" + "=" * 70)
    print("EXPERIMENT 35: Do we need the en-route GBT model?")
    print(f"Chains evaluated: {len(df)}")
    print(f"Avg time to sailing[1]: {results['horizons']['avg_mins_to_s1']:.0f} min")
    print(f"Avg time to sailing[2]: {results['horizons']['avg_mins_to_s2']:.0f} min")
    print("=" * 70)

    print("\n### Hop 0: Predict next sailing (the one users care about)")
    print(f"{'Approach':<25s} {'MAE':>6s} {'Bias':>6s} {'±3min':>6s} {'±5min':>6s}")
    print("-" * 55)
    for name, m in results["hop0"].items():
        print(
            f"{name:<25s} {m['mae']:>6.2f} {m['bias']:>+5.2f} {m['within_3']:>5.1f}% {m['within_5']:>5.1f}%"
        )

    print("\n### Hop 1: Predict 2 sailings out")
    print(f"{'Approach':<25s} {'MAE':>6s} {'Bias':>6s} {'±3min':>6s} {'±5min':>6s}")
    print("-" * 55)
    for name, m in results["hop1"].items():
        print(
            f"{name:<25s} {m['mae']:>6.2f} {m['bias']:>+5.2f} {m['within_3']:>5.1f}% {m['within_5']:>5.1f}%"
        )

    print("\n### Hop 1 by delay bucket")
    print(f"{'Bucket':<12s}", end="")
    approach_names = list(next(iter(results["hop1_buckets"].values())).keys())
    for name in approach_names:
        print(f" {name:>18s}", end="")
    print()
    print("-" * (12 + 19 * len(approach_names)))
    for bkt_name, bkt in results["hop1_buckets"].items():
        print(f"{bkt_name:<12s}", end="")
        for name in approach_names:
            print(f" {bkt['mae']:>18.2f}" if name in bkt else f" {'—':>18s}", end="")
            bkt_entry = bkt.get(name)
            if bkt_entry:
                print(
                    f"\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b\b{bkt_entry['mae']:>18.2f}",
                    end="",
                )
        print()

    # --- Verdict ---
    hop1_flat = results["hop1"]["Option A + flat"]["mae"]
    hop1_gbt = results["hop1"]["Option A + GBT"]["mae"]
    delta = hop1_flat - hop1_gbt
    print("\n### Verdict")
    print(f"GBT advantage at hop 1: {delta:+.2f} min MAE")
    if abs(delta) < 0.15:
        print("→ GBT adds negligible value. Drop it.")
    elif delta > 0:
        print(f"→ GBT helps by {delta:.2f} MAE. Consider keeping for future sailings.")
    else:
        print(f"→ GBT is WORSE by {-delta:.2f} MAE. Definitely drop it.")


if __name__ == "__main__":
    main()
