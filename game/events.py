"""Random day events. An event changes what the household wants today (target hours), not the rules.

Python applies the same changes the browser showed, so the official score matches what the player saw.
"""
from dataclasses import dataclass, replace

from .appliances import Appliance


@dataclass(frozen=True)
class Event:
    key: str
    name: str
    blurb: str
    changes: dict  # appliance key -> new target_hours


EVENTS = {
    e.key: e
    for e in [
        Event("heatwave", "Heatwave", "Temperatures soar. The household wants cooling for much longer today.",
              {"ac": 11, "fan": 14}),
        Event("guests", "Guests visiting", "Friends are coming over: more cooking, TV and light.",
              {"cooktop": 3, "tv": 7, "lights": 9}),
        Event("wfh", "Work-from-home day", "Everyone is online all day. The computer and lights are needed longer.",
              {"computer": 9, "lights": 8}),
        Event("laundry", "Laundry day", "A big pile of washing and ironing is waiting.",
              {"washer": 2, "iron": 2}),
        Event("coldsnap", "Cold snap", "A chilly spell. Everyone wants long hot showers.",
              {"heater": 3}),
    ]
}


def apply_event(appliances: list[Appliance], event_key: str | None) -> list[Appliance]:
    """Return appliances with the event's target-hour changes applied (unchanged if no/unknown event)."""
    event = EVENTS.get(event_key or "")
    if not event:
        return list(appliances)
    return [replace(a, target_hours=event.changes.get(a.key, a.target_hours)) for a in appliances]
