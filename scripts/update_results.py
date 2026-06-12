import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from openpyxl import load_workbook


EXCEL_SHARE_URL = os.environ.get("EXCEL_SHARE_URL", "").strip()
EXCEL_FILE = Path("latest-vm-tips.xlsm")
OUTPUT_FILE = Path("resultat.json")


def onedrive_share_to_download_url(url: str) -> str:
    """
    Converts a public 1drv.ms / OneDrive share URL to a Microsoft Graph anonymous download endpoint.
    This usually works for files shared with "anyone with the link can view".
    """
    encoded = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii").rstrip("=")
    return f"https://api.onedrive.com/v1.0/shares/u!{encoded}/root/content"


def download_excel() -> None:
    if not EXCEL_SHARE_URL:
        raise RuntimeError("EXCEL_SHARE_URL saknas")

    download_url = onedrive_share_to_download_url(EXCEL_SHARE_URL)
    headers = {
        "User-Agent": "Mozilla/5.0 GitHubActions VM-tipset updater"
    }

    response = requests.get(download_url, headers=headers, timeout=60, allow_redirects=True)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    content = response.content

    if len(content) < 50_000:
        raise RuntimeError(
            f"Nedladdningen verkar för liten ({len(content)} bytes). "
            f"Content-Type: {content_type}. Länken kanske inte ger direkt filåtkomst."
        )

    # XLSX/XLSM are zip files and should start with PK
    if not content.startswith(b"PK"):
        raise RuntimeError(
            "Nedladdningen ser inte ut som en Excel-fil. "
            f"Content-Type: {content_type}. Första bytes: {content[:20]!r}"
        )

    EXCEL_FILE.write_bytes(content)
    print(f"Laddade ner Excel: {len(content)} bytes")


def value(ws, row, col):
    return ws.cell(row=row, column=col).value


def read_leaderboard(ws):
    # Känd struktur i er fil:
    # HE = placering, HG = namn, HH = poäng
    leaderboard = []
    for row in range(4, 90):
        position = value(ws, row, 208)
        name = value(ws, row, 210)
        points = value(ws, row, 211)

        if name and points is not None:
            try:
                position = int(position)
            except Exception:
                position = len(leaderboard) + 1

            try:
                points = int(points)
            except Exception:
                pass

            leaderboard.append({
                "position": position,
                "name": str(name).strip(),
                "points": points
            })

    if not leaderboard:
        raise RuntimeError("Hittade ingen topplista. Kontrollera Excel-layouten/fliknamnet.")

    return leaderboard


def read_matches(ws):
    matches = []
    current_section = ""

    for row in range(2, 170):
        b = value(ws, row, 2)

        if isinstance(b, str):
            text = b.strip()
            if text and text not in ("Match", "Gruppspel / slutspel", "Fyll i resultat"):
                current_section = text

        match_no = value(ws, row, 2)
        date_val = value(ws, row, 3)
        home = value(ws, row, 4)
        away = value(ws, row, 6)
        home_goals = value(ws, row, 7)  # gulmarkerad resultatcell
        away_goals = value(ws, row, 9)  # gulmarkerad resultatcell

        if isinstance(match_no, (int, float)) and home and away:
            if hasattr(date_val, "strftime"):
                date = date_val.strftime("%Y-%m-%d")
            else:
                date = str(date_val) if date_val else ""

            played = home_goals is not None and away_goals is not None

            if played:
                try:
                    hg = int(home_goals)
                    ag = int(away_goals)
                    score = f"{hg}–{ag}"
                except Exception:
                    hg = home_goals
                    ag = away_goals
                    score = f"{home_goals}–{away_goals}"
            else:
                hg = None
                ag = None
                score = "–"

            matches.append({
                "section": current_section,
                "match": int(match_no),
                "date": date,
                "home": str(home).strip(),
                "away": str(away).strip(),
                "homeGoals": hg,
                "awayGoals": ag,
                "score": score,
                "status": "spelad" if played else "kommande"
            })

    return matches


def main():
    download_excel()

    workbook = load_workbook(EXCEL_FILE, data_only=True, keep_vba=True)

    if "Resultat & tabell" not in workbook.sheetnames:
        raise RuntimeError(f"Fliken 'Resultat & tabell' saknas. Flikar: {workbook.sheetnames}")

    ws = workbook["Resultat & tabell"]

    data = {
        "updated": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
        "leaderboard": read_leaderboard(ws),
        "matches": read_matches(ws),
    }

    OUTPUT_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Skapade {OUTPUT_FILE}")
    print(f"Deltagare: {len(data['leaderboard'])}")
    print(f"Matcher: {len(data['matches'])}")
    print(f"Spelade matcher: {sum(1 for m in data['matches'] if m['status'] == 'spelad')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FEL: {exc}", file=sys.stderr)
        sys.exit(1)
