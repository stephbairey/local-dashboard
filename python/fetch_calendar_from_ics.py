# Parse an ICS file and write next events to data/calendar.json
import sys, json, datetime as dt, configparser
from pathlib import Path

try:
    from icalendar import Calendar
except ImportError:
    raise SystemExit("Please: pip install icalendar")

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CFG = Path(__file__).resolve().parent / "config.ini"

def load_cfg():
    cp = configparser.ConfigParser()
    cp.read(CFG)
    return cp

def events_from_ics(path):
    text = Path(path).read_bytes()
    cal = Calendar.from_ical(text)
    events = []
    now = dt.datetime.now(dt.timezone.utc)
    for comp in cal.walk():
        if comp.name != "VEVENT":
            continue
        start = comp.get("DTSTART").dt
        end = comp.get("DTEND").dt if comp.get("DTEND") else None
        if isinstance(start, dt.datetime) and start.tzinfo is None:
            start = start.replace(tzinfo=dt.timezone.utc)
        if isinstance(end, dt.datetime) and end.tzinfo is None:
            end = end.replace(tzinfo=dt.timezone.utc)
        if isinstance(start, dt.date) and not isinstance(start, dt.datetime):
            # all-day converts to midnight UTC
            start = dt.datetime.combine(start, dt.time(0, 0), tzinfo=dt.timezone.utc)
        title = str(comp.get("SUMMARY", "Untitled"))
        location = str(comp.get("LOCATION", ""))
        if start >= now - dt.timedelta(days=1):
            events.append({
                "title": title,
                "start": start.astimezone().isoformat(),
                "end": end.astimezone().isoformat() if isinstance(end, dt.datetime) else None,
                "location": location
            })
    events.sort(key=lambda e: e["start"])
    return events[:20]

def main():
    cfg = load_cfg()
    ics_path = cfg.get("calendar", "ics_path", fallback="").strip()
    if not ics_path:
        raise SystemExit("Set calendar.ics_path in python/config.ini")
    events = events_from_ics(ics_path)
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "calendar.json").write_text(json.dumps({"events": events}, indent=2))

if __name__ == "__main__":
    main()
