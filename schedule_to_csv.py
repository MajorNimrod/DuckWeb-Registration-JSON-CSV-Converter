#!/usr/bin/env python3
import json
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Any

MAX_DURATION_MINUTES = 119
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def parse_iso_with_offset(s: str) -> datetime:
    if len(s) >= 5 and (s[-5] in "+-") and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    return datetime.fromisoformat(s)


def format_time(dt: datetime) -> str:
    hour = dt.hour
    minute = dt.minute
    ampm = "AM" if hour < 12 else "PM"
    hour = hour % 12
    if hour == 0:
        hour = 12
    return f"{hour}:{minute:02d} {ampm}"


def should_include_meeting(event: Dict[str, Any]) -> bool:
    start = parse_iso_with_offset(event["start"])
    end = parse_iso_with_offset(event["end"])
    duration_minutes = (end - start).total_seconds() / 60.0
    return duration_minutes < MAX_DURATION_MINUTES


def clean_title(raw_title: str, subject: str, course_number: str) -> str:
    t = (raw_title or "").strip()
    if t.startswith("+"):
        rest = t[1:].strip()
        if rest.lower().startswith("dis"):
            return f"{subject} {course_number} Discussion"
        if rest.lower().startswith("lab"):
            return f"{subject} {course_number} Lab"
        return rest
    return t


def process_events(events: List[Dict[str, Any]]) -> List[List[str]]:
    by_crn: Dict[str, Dict[str, Any]] = {}

    for e in events:
        if not should_include_meeting(e):
            continue

        crn = e["crn"]
        if crn not in by_crn:
            by_crn[crn] = {
                "term": e.get("term", ""),
                "crn": crn,
                "subject": e.get("subject", ""),
                "courseNumber": e.get("courseNumber", ""),
                "title": clean_title(
                    e.get("title", ""),
                    e.get("subject", ""),
                    e.get("courseNumber", ""),
                ),
                "meetings": [],
            }

        start_dt = parse_iso_with_offset(e["start"])
        end_dt = parse_iso_with_offset(e["end"])
        day_idx = start_dt.weekday()
        day_name = DAY_NAMES[day_idx]
        start_str = format_time(start_dt)
        end_str = format_time(end_dt)

        meetings = by_crn[crn]["meetings"]
        if not any(
            m["day"] == day_name and m["start"] == start_str and m["end"] == end_str
            for m in meetings
        ):
            meetings.append(
                {
                    "day_idx": day_idx,
                    "day": day_name,
                    "start": start_str,
                    "end": end_str,
                }
            )

    rows: List[List[str]] = []
    rows.append(["Term", "CRN", "Subject", "Course", "Title", "Meetings"])

    for course in by_crn.values():
        meetings_sorted = sorted(
            course["meetings"], key=lambda m: (m["day_idx"], m["start"])
        )
        meetings_str = "; ".join(
            f'{m["day"]} {m["start"]}-{m["end"]}' for m in meetings_sorted
        )

        rows.append(
            [
                str(course["term"]),
                str(course["crn"]),
                str(course["subject"]),
                str(course["courseNumber"]),
                str(course["title"]),
                meetings_str,
            ]
        )

    return rows


def extract_events_from_har(har: dict) -> List[Dict[str, Any]]:
    """
    Given a HAR file, find the first response whose body parses as
    a list of objects with 'crn', 'subject', 'courseNumber' keys.
    """
    entries = har.get("log", {}).get("entries", [])
    for entry in entries:
        content = entry.get("response", {}).get("content", {})
        text = content.get("text")
        if not text:
            continue
        try:
            data = json.loads(text)
        except Exception:
            continue
        if isinstance(data, list) and data and isinstance(data[0], dict):
            if all(
                any(k in ev for k in ("crn", "subject", "courseNumber"))
                for ev in data
            ):
                return data
    raise ValueError("Could not find registration JSON array in HAR file.")


def load_events(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # JSON array directly → use as events
    if isinstance(data, list):
        return data

    # HAR structure
    if isinstance(data, dict) and "log" in data:
        return extract_events_from_har(data)

    raise ValueError("Input is neither a JSON events array nor a HAR file.")


def main():
    parser = argparse.ArgumentParser(
        description="Convert DuckWeb-style registration JSON/HAR to a CSV schedule."
    )
    parser.add_argument(
        "input_file",
        help="Path to registration JSON (array) or HAR file exported from DevTools.",
    )
    parser.add_argument(
        "-o",
        "--output_csv",
        default="schedule.csv",
        help="Output CSV file path (default: schedule.csv).",
    )
    args = parser.parse_args()

    events = load_events(args.input_file)
    rows = process_events(events)

    with open(args.output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Wrote {len(rows) - 1} courses to {args.output_csv}")


if __name__ == "__main__":
    main()
