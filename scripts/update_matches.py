import json
import re
from html import unescape
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

SOURCE_URL = "https://www.espn.com/soccer/story/_/id/48939282/2026-fifa-world-cup-fixtures-results-match-schedule-group-stage-knockout-rounds-bracket"
OUTPUT_FILE = "matcher.json"

ET = ZoneInfo("America/New_York")
STOCKHOLM = ZoneInfo("Europe/Stockholm")

DAY_RE = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+([A-Za-z]+)\s+(\d{1,2}):?$")
RESULT_RE = re.compile(r"^Group ([A-L]):\s+(.+?)\s+(\d+)-(\d+)\s+(.+?)\s+\((.*?)\)")
UPCOMING_RE = re.compile(r"^Group ([A-L]):\s+(.+?)\s+vs\.?\s+(.+?)\s+\((.*?)\)(?:,\s*(.*))?$")
ET_TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(a|p)\.m\. ET(?:\s*\(([A-Za-z]+ \d{1,2})\))?", re.I)

def clean(text):
    text = unescape(text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text

def parse_swedish_time(time_text, base_date):
    if not time_text:
        return "", ""

    m = ET_TIME_RE.search(time_text)
    if not m:
        return "", ""

    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    ampm = m.group(3).lower()
    override_date = m.group(4)

    if ampm == "p" and hour != 12:
        hour += 12
    if ampm == "a" and hour == 12:
        hour = 0

    if override_date:
        dt_date = datetime.strptime(f"{override_date} 2026", "%B %d %Y")
    else:
        dt_date = base_date

    dt_et = datetime(2026, dt_date.month, dt_date.day, hour, minute, tzinfo=ET)
    dt_se = dt_et.astimezone(STOCKHOLM)

    return dt_se.strftime("%Y-%m-%d"), dt_se.strftime("%H:%M")

def main():
    response = requests.get(SOURCE_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text("\n")
    lines = [clean(line) for line in text.splitlines() if clean(line)]

    matches = []
    current_date = None

    for line in lines:
        day_match = DAY_RE.match(line)
        if day_match:
            month = day_match.group(2)
            day = day_match.group(3)
            current_date = datetime.strptime(f"{month} {day} 2026", "%B %d %Y")
            continue

        if not current_date:
            continue

        result_match = RESULT_RE.match(line)
        if result_match:
            group, home, hg, ag, away, venue = result_match.groups()
            matches.append({
                "date": current_date.strftime("%Y-%m-%d"),
                "time": "",
                "group": group,
                "home": home.strip(),
                "away": away.strip(),
                "venue": venue.strip(),
                "status": "spelad",
                "score": f"{hg}–{ag}",
                "source": "ESPN"
            })
            continue

        upcoming_match = UPCOMING_RE.match(line)
        if upcoming_match:
            group, home, away, venue, time_text = upcoming_match.groups()
            date_se, time_se = parse_swedish_time(time_text or "", current_date)

            matches.append({
                "date": date_se or current_date.strftime("%Y-%m-%d"),
                "time": time_se,
                "group": group,
                "home": home.strip(),
                "away": away.strip(),
                "venue": venue.strip(),
                "status": "kommande",
                "score": None,
                "source": "ESPN"
            })

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(matches, f, ensure_ascii=False, indent=2)

    print(f"Skapade {OUTPUT_FILE} med {len(matches)} matcher")

if __name__ == "__main__":
    main()
