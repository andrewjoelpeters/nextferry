# NextFerry

## Gotchas

- **WSDOT vessel data can have null fields even when the vessel is moving.** A vessel may report `AtDock: false` with non-zero speed but have `ScheduledDeparture`, `LeftDock`, and `Eta` all null. When matching vessel state to schedule sailings, always verify the direction (departing/arriving terminal) matches before annotating — don't assume the first future sailing corresponds to the vessel's current trip.
