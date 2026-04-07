import json
from datetime import datetime


def read_json():
    """read the lap pool events json file"""
    with open("lap_pool_week.json", encoding="utf-8") as f:
        return json.load(f)


def build_status(events: list):
    """Create a current status dict from the list of pool events"""
    now = datetime.now()

    current = None
    next_event = None
    active_events = []

    lap_lanes_in_use = 0
    non_lap_lanes_in_use = 0

    def is_lap_swim(event):
        return "Lap Swim" in event.get("title", "")

    for e in sorted(events, key=lambda x: x["start"]):
        start = datetime.fromisoformat(e["start"])
        end = datetime.fromisoformat(e["end"])
        is_active = start <= now <= end
        lanes = e.get("lanes") or 0

        if is_active:
            active_events.append(e["title"])

            if is_lap_swim(e):
                lap_lanes_in_use += lanes
                if current is None:
                    current = e
            else:
                non_lap_lanes_in_use += lanes

        if start > now and next_event is None and is_lap_swim(e):
            next_event = e

    lanes_free = min(lap_lanes_in_use, 6)
    lanes_used = min(non_lap_lanes_in_use, 6)

    if current and current.get("title", "").startswith("CANCELED:"):
        lanes_free = 0
        lanes_used = 6

    return {
        "current_time": now.isoformat(timespec="seconds"),
        "now": current.get("raw_title", current["title"]) if current else "None",
        "next": next_event.get("raw_title", next_event["title"]) if next_event else "None",
        "next_time": next_event["start"] if next_event else None,
        "lanes_used": lanes_used,
        "lanes_free": lanes_free,
        "active_events": active_events,
    }


def write_status(status: dict):
    """write the status to a json file"""
    with open("status.json", "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


def get_status():
    """Get the status json file"""
    data = read_json()
    status = build_status(data)
    write_status(status)


if __name__ == "__main__":
    get_status()
