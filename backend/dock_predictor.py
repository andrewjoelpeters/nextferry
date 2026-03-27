"""At-dock delay predictor.

Predicts departure delay for vessels currently at dock, using features like
how long the vessel has been docked, current car loading, and terminal.

Parallel to ml_predictor.py (en-route delay), this module owns:
- Data loading (build_training_data)
- Save/load orchestration
- The predict() API surface consumed by the serving layer
- The module-level singleton

Usage:
    python -m backend.dock_predictor
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from .config import ROUTES
from .database import get_connection, get_sailing_event_count
from .model_training.at_dock_model import (
    AT_DOCK_FEATURE_COLS,
    AtDockGBTModel,
)

logger = logging.getLogger(__name__)

MINIMUM_TRAINING_EVENTS = 200

_MODEL_FILENAME = "dock_model_v1.joblib"
_META_FILENAME = "dock_model_meta.joblib"


def get_volume_model_dir() -> Path:
    volume_path = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    data_dir = Path(volume_path) if volume_path else Path("./data")
    model_dir = data_dir / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    return model_dir


class DockPredictor:
    def __init__(self):
        self._model: AtDockGBTModel | None = None
        self.is_trained: bool = False
        self.last_trained: datetime | None = None
        self.last_evaluation: dict | None = None
        self.training_data_size: int = 0

    def build_training_data(self) -> pd.DataFrame | None:
        """Build training data from at-dock vessel snapshots.

        For each sailing event, finds all vessel_snapshots where at_dock=1
        for the same (vessel_id, scheduled_departure). Each snapshot becomes
        a training row with features observable at that moment.
        """
        from .database import get_training_data

        events = get_training_data()
        if len(events) < MINIMUM_TRAINING_EVENTS:
            logger.warning(
                f"Only {len(events)} sailing events, need {MINIMUM_TRAINING_EVENTS}"
            )
            return None

        conn = get_connection()
        try:
            events_df = pd.DataFrame(events)
            active_routes = {r["route_name"] for r in ROUTES}
            events_df = events_df[events_df["route_abbrev"].isin(active_routes)].copy()
            if len(events_df) < MINIMUM_TRAINING_EVENTS:
                logger.warning(
                    f"Only {len(events_df)} events for active routes, "
                    f"need {MINIMUM_TRAINING_EVENTS}"
                )
                return None

            events_df["departing_terminal_id"] = (
                events_df["departing_terminal_id"].fillna(0).astype(int)
            )
            events_df.rename(
                columns={
                    "delay_minutes": "actual_delay_minutes",
                    "id": "sailing_event_id",
                },
                inplace=True,
            )
            events_df["scheduled_departure_dt"] = pd.to_datetime(
                events_df["scheduled_departure"], format="ISO8601", utc=True
            ).dt.tz_localize(None)

            logger.info(
                f"Building at-dock training data from {len(events_df)} sailing events"
            )

            # --- At-dock snapshots: vessel sitting at terminal for each sailing ---
            vessel_ids = events_df["vessel_id"].unique().tolist()
            placeholders = ",".join("?" * len(vessel_ids))
            dock_df = pd.read_sql_query(
                f"""
                SELECT vessel_id, collected_at, scheduled_departure,
                       departing_terminal_id, speed
                FROM vessel_snapshots
                WHERE at_dock = 1
                  AND scheduled_departure IS NOT NULL AND scheduled_departure != ''
                  AND vessel_id IN ({placeholders})
                """,
                conn,
                params=vessel_ids,
            )
            if dock_df.empty:
                logger.warning("No at-dock snapshots found")
                return None

            dock_df["collected_at_dt"] = pd.to_datetime(
                dock_df["collected_at"], format="ISO8601", utc=True
            ).dt.tz_localize(None)
            dock_df["sched_dt"] = pd.to_datetime(
                dock_df["scheduled_departure"], format="ISO8601", utc=True
            ).dt.tz_localize(None)
            logger.info(f"Loaded {len(dock_df)} at-dock snapshots")

            # Join dock snapshots to sailing events on (vessel_id, scheduled_departure)
            merged = dock_df.merge(
                events_df[
                    [
                        "sailing_event_id",
                        "vessel_id",
                        "scheduled_departure",
                        "actual_delay_minutes",
                        "route_abbrev",
                        "day_of_week",
                        "hour_of_day",
                    ]
                ],
                on=["vessel_id", "scheduled_departure"],
                how="inner",
            )
            logger.info(
                f"Joined to {len(merged)} at-dock rows "
                f"({merged['sailing_event_id'].nunique()} events)"
            )

            if merged.empty:
                logger.warning("No at-dock snapshots matched sailing events")
                return None

            # --- Compute minutes_at_dock ---
            # For each (vessel_id, scheduled_departure), find the earliest at-dock snapshot
            first_dock = (
                merged.groupby(["vessel_id", "scheduled_departure"])["collected_at_dt"]
                .min()
                .reset_index()
                .rename(columns={"collected_at_dt": "first_docked_at"})
            )
            merged = merged.merge(
                first_dock, on=["vessel_id", "scheduled_departure"], how="left"
            )
            merged["minutes_at_dock"] = (
                (
                    merged["collected_at_dt"] - merged["first_docked_at"]
                ).dt.total_seconds()
                / 60
            ).clip(lower=0)

            # --- minutes_until_scheduled_departure ---
            merged["minutes_until_scheduled_departure"] = (
                (merged["sched_dt"] - merged["collected_at_dt"]).dt.total_seconds() / 60
            ).clip(lower=0)

            # --- Current fullness from sailing_space_snapshots ---
            logger.info("Loading sailing space snapshots for fullness...")
            fullness_df = pd.read_sql_query(
                """
                SELECT departing_terminal_id, departure_time, collected_at,
                       max_space_count, drive_up_space_count
                FROM sailing_space_snapshots
                WHERE max_space_count > 0
                """,
                conn,
            )
            if not fullness_df.empty:
                fullness_df["collected_at_dt"] = pd.to_datetime(
                    fullness_df["collected_at"], format="ISO8601", utc=True
                ).dt.tz_localize(None)
                fullness_df["departure_time_dt"] = pd.to_datetime(
                    fullness_df["departure_time"], format="ISO8601", utc=True
                ).dt.tz_localize(None)
                fullness_df["current_fullness"] = (
                    1.0
                    - fullness_df["drive_up_space_count"]
                    / fullness_df["max_space_count"]
                )

                # For each at-dock snapshot, find the most recent space snapshot
                # for the same terminal and departure time
                # Match on (departing_terminal_id, departure_time ≈ scheduled_departure)
                # and collected_at <= snapshot time
                fullness_parts = []
                for terminal_id in merged["departing_terminal_id"].unique():
                    m_term = merged.loc[
                        merged["departing_terminal_id"] == terminal_id
                    ].sort_values("collected_at_dt")
                    f_term = fullness_df.loc[
                        fullness_df["departing_terminal_id"] == terminal_id
                    ].sort_values("collected_at_dt")
                    if f_term.empty:
                        continue
                    matched = pd.merge_asof(
                        m_term[["sailing_event_id", "collected_at_dt", "collected_at"]],
                        f_term[["collected_at_dt", "current_fullness"]],
                        on="collected_at_dt",
                        direction="backward",
                        suffixes=("", "_space"),
                    )
                    fullness_parts.append(
                        matched[
                            ["sailing_event_id", "collected_at", "current_fullness"]
                        ]
                    )

                if fullness_parts:
                    fullness_result = pd.concat(fullness_parts, ignore_index=True)
                    merged = merged.merge(
                        fullness_result,
                        on=["sailing_event_id", "collected_at"],
                        how="left",
                    )
                else:
                    merged["current_fullness"] = np.nan
            else:
                merged["current_fullness"] = np.nan
            logger.info("Fullness features joined")

            # --- Incoming vehicle fullness (how full was the inbound trip?) ---
            # For a vessel at dock at terminal X, the inbound trip is the most
            # recent sailing that ARRIVED at X (arriving_terminal_id = X).
            # Its final fullness snapshot approximates how many cars needed to
            # unload, which affects turnaround time and delay propagation.
            logger.info("Loading inbound fullness...")
            inbound_df = pd.read_sql_query(
                """
                SELECT arriving_terminal_id, departure_time, collected_at,
                       max_space_count, drive_up_space_count
                FROM sailing_space_snapshots
                WHERE max_space_count > 0
                """,
                conn,
            )
            if not inbound_df.empty:
                inbound_df["collected_at_dt"] = pd.to_datetime(
                    inbound_df["collected_at"], format="ISO8601", utc=True
                ).dt.tz_localize(None)
                inbound_df["departure_time_dt"] = pd.to_datetime(
                    inbound_df["departure_time"], format="ISO8601", utc=True
                ).dt.tz_localize(None)
                inbound_df["inbound_fullness"] = (
                    1.0
                    - inbound_df["drive_up_space_count"] / inbound_df["max_space_count"]
                )

                # For each inbound sailing, keep only the last snapshot
                # (closest to departure = best estimate of final load)
                last_snap = (
                    inbound_df.sort_values("collected_at_dt")
                    .groupby(["arriving_terminal_id", "departure_time"])
                    .last()
                    .reset_index()
                )

                # For each at-dock row, find the most recent inbound sailing
                # arriving at this terminal before the vessel docked
                inbound_parts = []
                for terminal_id in merged["departing_terminal_id"].unique():
                    m_term = merged.loc[
                        merged["departing_terminal_id"] == terminal_id
                    ].sort_values("collected_at_dt")
                    i_term = last_snap.loc[
                        last_snap["arriving_terminal_id"] == terminal_id
                    ].sort_values("departure_time_dt")
                    if i_term.empty:
                        continue
                    matched = pd.merge_asof(
                        m_term[["sailing_event_id", "collected_at_dt", "collected_at"]],
                        i_term[["departure_time_dt", "inbound_fullness"]].rename(
                            columns={"departure_time_dt": "collected_at_dt"}
                        ),
                        on="collected_at_dt",
                        direction="backward",
                    )
                    inbound_parts.append(
                        matched[
                            ["sailing_event_id", "collected_at", "inbound_fullness"]
                        ]
                    )

                if inbound_parts:
                    inbound_result = pd.concat(inbound_parts, ignore_index=True)
                    merged = merged.merge(
                        inbound_result,
                        on=["sailing_event_id", "collected_at"],
                        how="left",
                    )
                    merged.rename(
                        columns={"inbound_fullness": "incoming_vehicle_fullness"},
                        inplace=True,
                    )
                else:
                    merged["incoming_vehicle_fullness"] = np.nan
            else:
                merged["incoming_vehicle_fullness"] = np.nan
            logger.info("Inbound fullness features joined")

            # --- Previous vessel delay (from a different sailing) ---
            logger.info("Loading previous vessel delays...")
            delays_df = pd.read_sql_query(
                f"""
                SELECT vessel_id, collected_at, scheduled_departure AS snap_sched_dep,
                       (julianday(left_dock) - julianday(scheduled_departure)) * 24 * 60
                           AS snap_delay_minutes
                FROM vessel_snapshots
                WHERE left_dock IS NOT NULL AND scheduled_departure IS NOT NULL
                  AND left_dock != '' AND scheduled_departure != ''
                  AND vessel_id IN ({placeholders})
                """,
                conn,
                params=vessel_ids,
            )
            if not delays_df.empty:
                delays_df["collected_at_dt"] = pd.to_datetime(
                    delays_df["collected_at"], format="ISO8601", utc=True
                ).dt.tz_localize(None)
                delays_df.sort_values(["vessel_id", "collected_at_dt"], inplace=True)

                merged.sort_values("collected_at_dt", inplace=True)
                delays_df.sort_values("collected_at_dt", inplace=True)
                merged = pd.merge_asof(
                    merged,
                    delays_df[
                        [
                            "vessel_id",
                            "collected_at_dt",
                            "snap_sched_dep",
                            "snap_delay_minutes",
                        ]
                    ],
                    on="collected_at_dt",
                    by="vessel_id",
                    direction="backward",
                    suffixes=("", "_delay"),
                )
                # Exclude same-sailing snapshots
                same_sailing = merged["snap_sched_dep"] == merged["scheduled_departure"]
                merged.loc[same_sailing, "snap_delay_minutes"] = np.nan
                merged["current_vessel_delay_minutes"] = merged[
                    "snap_delay_minutes"
                ].fillna(0.0)
            else:
                merged["current_vessel_delay_minutes"] = 0.0
            logger.info("Previous delay features joined")

        finally:
            conn.close()

        # --- Feature engineering ---
        merged["is_weekend"] = merged["day_of_week"].isin([0, 6]).astype(int)
        merged["departing_terminal_id"] = (
            merged["departing_terminal_id"].fillna(0).astype(int)
        )

        # Only keep snapshots collected before the scheduled departure
        # (predicting after departure time doesn't help)
        merged = merged[merged["minutes_until_scheduled_departure"] >= 0]

        result = merged[
            [
                "sailing_event_id",
                "vessel_id",
                "route_abbrev",
                "departing_terminal_id",
                "day_of_week",
                "hour_of_day",
                "is_weekend",
                "minutes_until_scheduled_departure",
                "minutes_at_dock",
                "current_fullness",
                "incoming_vehicle_fullness",
                "current_vessel_delay_minutes",
                "actual_delay_minutes",
            ]
        ].copy()

        if result.empty:
            logger.warning("No training rows generated")
            return None

        logger.info(
            f"Built at-dock training data: {len(result)} rows from "
            f"{result['sailing_event_id'].nunique()} sailing events"
        )
        return result

    def train(self) -> bool:
        df = self.build_training_data()
        if df is None:
            return False

        unique_events = df["sailing_event_id"].unique()
        split_idx = int(len(unique_events) * 0.8)
        train_events = set(unique_events[:split_idx])
        test_events = set(unique_events[split_idx:])

        train_mask = df["sailing_event_id"].isin(train_events)
        test_mask = df["sailing_event_id"].isin(test_events)

        train_df = df[train_mask]
        test_df = df[test_mask].copy()

        logger.info(f"Training on {len(train_df)} rows, testing on {len(test_df)} rows")

        eval_model = AtDockGBTModel()
        eval_model.fit(train_df)

        if len(test_df) > 0:
            from .model_training.evaluation import evaluate_predictions

            test_df = eval_model.predict(test_df)
            self.last_evaluation = evaluate_predictions(test_df)
            logger.info(f"Evaluation: {self.last_evaluation}")

        # Train production model on all data
        self._model = AtDockGBTModel()
        self._model.fit(df)
        self.is_trained = True
        self.last_trained = datetime.now()
        self.training_data_size = len(df)

        return True

    def predict(
        self,
        route_abbrev: str,
        departing_terminal_id: int,
        vessel_id: int,
        day_of_week: int,
        hour_of_day: int,
        minutes_until_scheduled_departure: float,
        minutes_at_dock: float,
        current_fullness: float | None = None,
        incoming_vehicle_fullness: float | None = None,
        current_vessel_delay_minutes: float = 0.0,
    ) -> dict | None:
        if not self.is_trained or self._model is None:
            return None

        # Convert Python weekday (Mon=0..Sun=6) to SQLite strftime %w (Sun=0..Sat=6)
        dow = day_of_week + 1 if day_of_week != 6 else 0

        try:
            return self._model.predict_single(
                route_abbrev=route_abbrev,
                departing_terminal_id=departing_terminal_id,
                vessel_id=vessel_id,
                day_of_week=dow,
                hour_of_day=hour_of_day,
                minutes_until_scheduled_departure=minutes_until_scheduled_departure,
                minutes_at_dock=minutes_at_dock,
                current_fullness=current_fullness,
                incoming_vehicle_fullness=incoming_vehicle_fullness,
                current_vessel_delay_minutes=current_vessel_delay_minutes,
            )
        except ValueError as e:
            logger.error(f"At-dock prediction failed: {e}")
            return None

    def save(self, path: Path | None = None):
        if self._model is None:
            return
        model_dir = path or get_volume_model_dir()
        model_dir.mkdir(parents=True, exist_ok=True)
        self._model.save(model_dir / _MODEL_FILENAME)
        joblib.dump(
            {
                "last_trained": self.last_trained,
                "training_data_size": self.training_data_size,
                "last_evaluation": self.last_evaluation,
            },
            model_dir / _META_FILENAME,
        )
        logger.info(f"At-dock model saved to {model_dir}")

    def load(self, path: Path | None = None) -> bool:
        model_dir = path or get_volume_model_dir()
        model_path = model_dir / _MODEL_FILENAME
        if not model_path.exists():
            logger.info("No saved at-dock model found")
            return False

        try:
            model = AtDockGBTModel.load(model_path)
            if model is None:
                logger.warning("Failed to load at-dock model from disk")
                return False
            if model._feature_cols != AT_DOCK_FEATURE_COLS:
                logger.warning(
                    f"At-dock model has stale features "
                    f"({len(model._feature_cols)} vs {len(AT_DOCK_FEATURE_COLS)}), "
                    f"skipping — will retrain"
                )
                return False
            self._model = model
            meta = joblib.load(model_dir / _META_FILENAME)
            self.last_trained = meta["last_trained"]
            self.training_data_size = meta["training_data_size"]
            self.last_evaluation = meta.get("last_evaluation")
            self.is_trained = True
            logger.info(
                f"At-dock model loaded from {model_dir} (trained: {self.last_trained})"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to load at-dock model: {e}")
            return False


# Module-level singleton
dock_predictor = DockPredictor()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    from .database import init_db

    init_db()

    event_count = get_sailing_event_count()
    print(f"Sailing events in database: {event_count}")

    if event_count < MINIMUM_TRAINING_EVENTS:
        print(
            f"Need at least {MINIMUM_TRAINING_EVENTS} events to train. "
            f"Currently have {event_count}."
        )
    else:
        success = dock_predictor.train()
        if success:
            dock_predictor.save()
            print(f"At-dock model trained on {dock_predictor.training_data_size} rows")
            if dock_predictor.last_evaluation:
                print(f"Evaluation: {dock_predictor.last_evaluation}")
        else:
            print("Training failed")
