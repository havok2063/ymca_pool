import argparse
import json
import re
from datetime import datetime, timedelta
from html import unescape
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ACCOUNT_ID = 988
LOCATION_ID = 5961
STUDIO_ID = "30110"
URL = "https://www.groupexpro.com/schedule/embed/json_schedule.php"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAY_INDEX = {d: i for i, d in enumerate(DAY_ORDER)}

# Fixed schedules: Swim Team and Lessons
# These are treated as atomic/fixed per the pool schedule.
SWIM_TEAM_SCHEDULE = {
    "Monday": [
        {"start": "16:30", "end": "17:45", "lanes": 3, "lane_start": 3, "lane_span": 3},
        {"start": "17:45", "end": "19:15", "lanes": 3, "lane_start": 3, "lane_span": 3},
        {"start": "19:15", "end": "20:45", "lanes": 2, "lane_start": 4, "lane_span": 2},
    ],
    "Tuesday": [
        {"start": "16:30", "end": "17:45", "lanes": 3, "lane_start": 3, "lane_span": 3},
        {"start": "17:45", "end": "19:15", "lanes": 3, "lane_start": 3, "lane_span": 3},
        {"start": "19:15", "end": "20:45", "lanes": 2, "lane_start": 4, "lane_span": 2},
    ],
    "Wednesday": [
        {"start": "16:30", "end": "17:30", "lanes": 4, "lane_start": 2, "lane_span": 4},
        {"start": "17:30", "end": "19:00", "lanes": 3, "lane_start": 3, "lane_span": 3},
        {"start": "19:00", "end": "20:45", "lanes": 2, "lane_start": 4, "lane_span": 2},
    ],
    "Thursday": [
        {"start": "16:30", "end": "17:45", "lanes": 3, "lane_start": 3, "lane_span": 3},
        {"start": "17:45", "end": "19:15", "lanes": 3, "lane_start": 3, "lane_span": 3},
        {"start": "19:15", "end": "20:45", "lanes": 2, "lane_start": 4, "lane_span": 2},
    ],
    "Friday": [
        {"start": "16:30", "end": "17:30", "lanes": 4, "lane_start": 2, "lane_span": 4},
        {"start": "17:30", "end": "19:00", "lanes": 3, "lane_start": 3, "lane_span": 3},
        {"start": "19:00", "end": "20:30", "lanes": 2, "lane_start": 4, "lane_span": 2},
    ],
    "Saturday": [],
    "Sunday": [
        {"start": "08:00", "end": "09:15", "lanes": 3, "lane_start": 3, "lane_span": 3},
        {"start": "09:15", "end": "10:45", "lanes": 3, "lane_start": 3, "lane_span": 3},
    ],
}

# Lessons schedule
LESSONS_SCHEDULE = {
    "Monday": [
        {"start": "12:30", "end": "13:30", "lanes": 1, "lane_start": 0, "lane_span": 1},
        {"start": "16:00", "end": "17:45", "lanes": 1, "lane_start": 0, "lane_span": 1},
        {"start": "17:45", "end": "20:00", "lanes": 2, "lane_start": 0, "lane_span": 2},
    ],
    "Tuesday": [
        {"start": "16:00", "end": "16:30", "lanes": 1, "lane_start": 0, "lane_span": 1},
        {"start": "16:30", "end": "20:00", "lanes": 2, "lane_start": 0, "lane_span": 2},
        {"start": "20:00", "end": "20:30", "lanes": 1, "lane_start": 0, "lane_span": 1},
    ],
    "Wednesday": [
        {"start": "16:00", "end": "16:30", "lanes": 1, "lane_start": 0, "lane_span": 1},
        {"start": "16:30", "end": "20:00", "lanes": 2, "lane_start": 0, "lane_span": 2},
    ],
    "Thursday": [
        {"start": "16:00", "end": "20:30", "lanes": 2, "lane_start": 0, "lane_span": 2},
    ],
    "Friday": [
        {"start": "16:00", "end": "20:30", "lanes": 1, "lane_start": 0, "lane_span": 1},
    ],
    "Saturday": [
        {"start": "08:00", "end": "12:00", "lanes": 2, "lane_start": 0, "lane_span": 2},
        {"start": "12:00", "end": "14:15", "lanes": 1, "lane_start": 0, "lane_span": 1},
    ],
    "Sunday": [
        {"start": "08:00", "end": "12:00", "lanes": 2, "lane_start": 0, "lane_span": 2},
    ],
}


def fetch_wrapped_json(params: dict) -> dict:
    """Fetch the schedule data and convert to json data"""
    query = urlencode(params)
    request = Request(f"{URL}?{query}", headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8", errors="replace").strip()
    match = re.search(r"^(?:[A-Za-z0-9_$.]+\s*)?\(\s*(.*)\s*\)\s*;?\s*$", text, re.DOTALL)
    if not match:
        raise ValueError(f"Could not parse wrapped JSON response: {text[:300]}")
    return json.loads(match.group(1))


def week_monday_to_sunday() -> tuple[datetime, datetime]:
    """Get the current week's Monday and Sunday datetimes"""
    now = datetime.now()
    monday = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def strip_html(text: str) -> str:
    """Strip HTML tags from a string."""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", unescape(text)).strip()


def parse_time_range(date_str: str, time_range: str) -> tuple[datetime, datetime]:
    """Parse date and time range into start and end datetimes"""
    start_s, end_s = [x.strip() for x in time_range.split("-", 1)]
    start_dt = datetime.strptime(f"{date_str} {start_s}", "%A, %B %d, %Y %I:%M%p")
    end_dt = datetime.strptime(f"{date_str} {end_s}", "%A, %B %d, %Y %I:%M%p")
    return start_dt, end_dt


def clean_title(title: str) -> str:
    """Clean the event title to remove lane counts"""
    return re.sub(r"\s*\(\d+\s+lane[s]?\)\s*$", "", title, flags=re.IGNORECASE).strip()


def extract_lane_count(title: str) -> Optional[int]:
    """Extract lane count from the title"""
    match = re.search(r"\((\d+)\s+lane[s]?\)", title, re.IGNORECASE)
    return int(match.group(1)) if match else None


def minutes_since_midnight(dt: datetime) -> int:
    """Get the minutes since midnight for a given datetime"""
    return dt.hour * 60 + dt.minute


def format_time_label(dt: datetime) -> str:
    """Format time label"""
    return dt.strftime("%I:%M%p").lstrip("0").lower()


def is_swim_team_season(date_obj: datetime) -> bool:
    """Swim Team is active from September through May."""
    return date_obj.month >= 9 or date_obj.month <= 5


def parse_schedule_rows(payload: dict) -> list[dict]:
    """Parse the schedule rows from the API payload into a list of event dicts"""
    events: list[dict] = []
    for row in payload.get("aaData", []):
        if len(row) < 6:
            continue

        date_str = row[0]
        time_range = row[1]
        raw_title = strip_html(row[2])
        category = strip_html(row[5])

        start_dt, end_dt = parse_time_range(date_str, time_range)
        title = clean_title(raw_title)
        lanes = extract_lane_count(raw_title)

        if title.lower() == "swim team" and not is_swim_team_season(start_dt):
            continue

        event = {
            "day": start_dt.strftime("%A"),
            "date": start_dt.strftime("%Y-%m-%d"),
            "start": start_dt.isoformat(timespec="seconds"),
            "end": end_dt.isoformat(timespec="seconds"),
            "start_time": format_time_label(start_dt),
            "end_time": format_time_label(end_dt),
            "title": title,
            "raw_title": raw_title,
            "lanes": lanes,
            "category": category,
        }
        events.append(event)

    return events


def infer_lane_placement(event: dict) -> dict:
    """Infer basic lane_start/lane_span for API events."""
    title = event["title"].lower()
    start_dt = datetime.fromisoformat(event["start"])
    lanes = event.get("lanes")

    # Fixed lane rules for aqua fitness blocks.
    if (
        "aqua zumba" in title
        or "aqua arthritis" in title
        or "aqua arthritist" in title
        or "water fitness cardio" in title
        or "water fitness" in title
    ):
        lanes = 4
        lane_start = 0
    elif "deep water jog" in title:
        lanes = 4 if start_dt.hour < 12 else 3
        lane_start = 0
    elif "water walking" in title:
        lanes = lanes or 1
        lane_start = 0
    elif "lap swim" in title:
        lanes = lanes or 6
        lane_start = max(0, 6 - lanes)
    else:
        lanes = lanes or 6
        lane_start = max(1, (6 - lanes) // 2)

    lanes = max(1, min(6, lanes))
    lane_start = max(0, min(6 - lanes, lane_start))

    return {
        "lane_start": lane_start,
        "lane_span": lanes,
    }


def add_fixed_schedule(events: list[dict], week_start: datetime) -> None:
    """Add Swim Team and Lessons events using fixed schedule."""
    day_date_map = {e["day"]: e["date"] for e in events}

    for day in DAY_ORDER:
        if day not in day_date_map:
            day_offset = DAY_INDEX[day]
            day_date_map[day] = (week_start + timedelta(days=day_offset)).strftime("%Y-%m-%d")

    # Check which events already exist to avoid duplicates
    existing_keys = set()
    for e in events:
        start_dt = datetime.fromisoformat(e["start"])
        end_dt = datetime.fromisoformat(e["end"])
        existing_keys.add(
            (
                e["day"],
                minutes_since_midnight(start_dt),
                minutes_since_midnight(end_dt),
                e["title"].lower(),
            )
        )

    # Add Swim Team blocks only in-season (September-May)
    for day, blocks in SWIM_TEAM_SCHEDULE.items():
        date_str = day_date_map.get(day)
        if not date_str:
            continue

        day_dt = datetime.fromisoformat(f"{date_str}T00:00:00")
        if not is_swim_team_season(day_dt):
            continue

        for block in blocks:
            start_dt = datetime.fromisoformat(f"{date_str}T{block['start']}:00")
            end_dt = datetime.fromisoformat(f"{date_str}T{block['end']}:00")
            key = (day, minutes_since_midnight(start_dt), minutes_since_midnight(end_dt), "swim team")

            if key in existing_keys:
                continue

            events.append(
                {
                    "day": day,
                    "date": date_str,
                    "start": start_dt.isoformat(timespec="seconds"),
                    "end": end_dt.isoformat(timespec="seconds"),
                    "start_time": format_time_label(start_dt),
                    "end_time": format_time_label(end_dt),
                    "title": "Swim Team",
                    "raw_title": f"Swim Team ({block['lanes']} lanes)",
                    "lanes": block["lanes"],
                    "category": "fixed",
                    "lane_start": block["lane_start"],
                    "lane_span": block["lane_span"],
                }
            )

    # Add Lessons blocks
    for day, blocks in LESSONS_SCHEDULE.items():
        date_str = day_date_map.get(day)
        if not date_str:
            continue

        for block in blocks:
            start_dt = datetime.fromisoformat(f"{date_str}T{block['start']}:00")
            end_dt = datetime.fromisoformat(f"{date_str}T{block['end']}:00")
            key = (day, minutes_since_midnight(start_dt), minutes_since_midnight(end_dt), "lessons")

            if key in existing_keys:
                continue

            events.append(
                {
                    "day": day,
                    "date": date_str,
                    "start": start_dt.isoformat(timespec="seconds"),
                    "end": end_dt.isoformat(timespec="seconds"),
                    "start_time": format_time_label(start_dt),
                    "end_time": format_time_label(end_dt),
                    "title": "Lessons",
                    "raw_title": f"Lessons ({block['lanes']} lanes)",
                    "lanes": block["lanes"],
                    "category": "fixed",
                    "lane_start": block["lane_start"],
                    "lane_span": block["lane_span"],
                }
            )


def sort_events(events: list[dict]) -> list[dict]:
    """Sort events by day, start time, end time, and title."""
    return sorted(
        events,
        key=lambda e: (
            DAY_INDEX.get(e["day"], 999),
            datetime.fromisoformat(e["start"]),
            datetime.fromisoformat(e["end"]),
            e["title"],
        ),
    )


def adjust_evening_lap_swim_position(events: list[dict]) -> None:
    """Place weekday evening Lap Swim (1-3 lanes) to the left of overlapping Swim Team blocks."""
    weekday_set = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}

    events_by_date: dict[str, list[dict]] = {}
    for event in events:
        events_by_date.setdefault(event["date"], []).append(event)

    for date_events in events_by_date.values():
        swim_team_blocks = [
            e
            for e in date_events
            if e.get("title", "").lower() == "swim team"
        ]

        if not swim_team_blocks:
            continue

        for lap in date_events:
            if lap.get("day") not in weekday_set:
                continue
            if lap.get("title", "").lower() != "lap swim":
                continue

            lanes = int(lap.get("lanes") or 0)
            if lanes < 1 or lanes > 3:
                continue

            lap_start = datetime.fromisoformat(lap["start"])
            if lap_start.hour < 16:
                continue

            lap_end = datetime.fromisoformat(lap["end"])
            lap_start_min = minutes_since_midnight(lap_start)
            lap_end_min = minutes_since_midnight(lap_end)

            for swim in swim_team_blocks:
                swim_start = datetime.fromisoformat(swim["start"])
                swim_end = datetime.fromisoformat(swim["end"])
                swim_start_min = minutes_since_midnight(swim_start)
                swim_end_min = minutes_since_midnight(swim_end)

                overlaps = lap_start_min < swim_end_min and lap_end_min > swim_start_min
                if not overlaps:
                    continue

                swim_lane_start = int(swim.get("lane_start", 3))
                lap["lane_start"] = max(0, min(6 - lanes, swim_lane_start - lanes))
                lap["lane_span"] = lanes
                break


def fetch_schedule() -> None:
    """Fetch the schedule and write to a JSON file."""
    parser = argparse.ArgumentParser(description="Fetch YMCA pool schedule with fixed Lessons/Swim Team blocks.")
    parser.add_argument("--output", default="lap_pool_week.json", help="Output JSON path")
    args = parser.parse_args()

    week_start, week_end = week_monday_to_sunday()

    payload = fetch_wrapped_json(
        {
            "schedule": "",
            "instructor_id": "true",
            "format": "jsonp",
            "a": ACCOUNT_ID,
            "location": LOCATION_ID,
            "studio": STUDIO_ID,
            "start": int(week_start.timestamp()),
            "end": int((week_end + timedelta(days=1)).timestamp()),
        }
    )

    events = parse_schedule_rows(payload)

    # For API events, add basic lane placement
    for event in events:
        placement = infer_lane_placement(event)
        event["lane_start"] = placement["lane_start"]
        event["lane_span"] = placement["lane_span"]
        event["lanes"] = placement["lane_span"]

    # Add fixed Swim Team and Lessons
    add_fixed_schedule(events, week_start)

    # Position weekday evening Lap Swim blocks to the left of Swim Team blocks.
    adjust_evening_lap_swim_position(events)

    events = sort_events(events)

    Path(args.output).write_text(json.dumps(events, indent=2), encoding="utf-8")

    print(f"Wrote {len(events)} events to {args.output}")
    print(f"Week: {week_start.date()} to {week_end.date()}")


if __name__ == "__main__":
    fetch_schedule()
