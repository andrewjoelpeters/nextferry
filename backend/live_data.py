"""Build the JSON payload served by the live map."""

from datetime import timedelta
from typing import Any

from .database import get_docked_since
from .serializers import Vessel
from .utils import datetime_to_minutes


def build_ferry_data(vessels: list[Vessel]) -> list[dict[str, Any]]:
    """Return enriched vessel data with dock and delay fields."""
    result = []
    for v in vessels:
        data = v.model_dump(mode="json", by_alias=True)

        # Add docked_since from DB snapshots when WSDOT Eta is null
        if v.at_dock and v.eta is None and v.scheduled_departure:
            docked_since = get_docked_since(
                v.vessel_id, v.scheduled_departure.isoformat()
            )
            data["DockedSince"] = docked_since.isoformat() if docked_since else None
        else:
            data["DockedSince"] = None

        # Add computed delay fields (not in WSDOT response)
        if v.delay is not None:
            delay_minutes = datetime_to_minutes(v.delay)
            data["DelayMinutes"] = delay_minutes
            if v.scheduled_departure:
                predicted = v.scheduled_departure + timedelta(minutes=delay_minutes)
                data["PredictedDeparture"] = predicted.isoformat()
            else:
                data["PredictedDeparture"] = None
        else:
            data["DelayMinutes"] = None
            data["PredictedDeparture"] = None

        result.append(data)
    return result
