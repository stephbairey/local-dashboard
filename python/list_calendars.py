# list_calendars.py
import json
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CREDS_FILE = Path(__file__).resolve().parent / "credentials.json"
TOKEN_FILE = Path(__file__).resolve().parent / "token.json"

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def get_creds():
    if not TOKEN_FILE.exists():
        raise SystemExit("No token.json yet. Run fetch_calendar_google.py once to create it.")
    return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

def main():
    creds = get_creds()
    service = build("calendar", "v3", credentials=creds)

    calendars = []
    page_token = None
    while True:
        resp = service.calendarList().list(pageToken=page_token).execute()
        items = resp.get("items", [])
        for c in items:
            calendars.append({
                "id": c.get("id"),
                "summary": c.get("summary"),
                "primary": c.get("primary", False),
                "accessRole": c.get("accessRole"),
                "hidden": c.get("hidden", False),
                "selected": c.get("selected", None),  # may be None on some accounts
            })
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    DATA.mkdir(parents=True, exist_ok=True)
    out = DATA / "calendars.json"
    out.write_text(json.dumps({"calendars": calendars}, indent=2), encoding="utf-8")

    print("\nFound calendars:\n")
    for c in calendars:
        sel = "Y" if c.get("selected") else "N" if c.get("selected") is not None else "-"
        hid = "Y" if c.get("hidden") else "N"
        prim = "Y" if c.get("primary") else "N"
        print(f"- {c['summary']!s:30}  primary:{prim}  hidden:{hid}  selected:{sel}  role:{c.get('accessRole')}  id:{c['id']}")

    print(f"\nWrote {out}")
    
if __name__ == "__main__":
    try:
        main()
    except HttpError as err:
        print(f"Google API error: {err}")
