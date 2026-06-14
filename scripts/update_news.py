import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

import requests

RSS_URL = "https://www.fotbollskanalen.se/rss/"
OUTPUT_FILE = "nyheter.json"

KEYWORDS = [
    "vm",
    "vm 2026",
    "fotbolls-vm",
    "världsmästerskapet",
    "sverige",
    "landslaget"
]

def clean(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    return " ".join(text.split())

def main():
    response = requests.get(RSS_URL, timeout=30)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items = root.findall(".//item")

    news = []

    for item in items:
        title = clean(item.findtext("title"))
        link = clean(item.findtext("link"))
        description = clean(item.findtext("description"))
        pub_date_raw = item.findtext("pubDate") or ""

        haystack = f"{title} {description}".lower()

        if not any(k in haystack for k in KEYWORDS):
            continue

        published = ""
        try:
            published = parsedate_to_datetime(pub_date_raw).strftime("%Y-%m-%d %H:%M")
        except Exception:
            published = pub_date_raw

        news.append({
            "title": title,
            "source": "Fotbollskanalen",
            "published": published,
            "summary": description[:220],
            "url": link
        })

        if len(news) >= 8:
            break

    if not news:
        news = [{
            "title": "Inga VM-nyheter hittades just nu",
            "source": "Fotbollskanalen",
            "published": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "summary": "Flödet kontrollerades men inga artiklar matchade VM-filter just nu.",
            "url": "https://www.fotbollskanalen.se/"
        }]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)

    print(f"Skapade {OUTPUT_FILE} med {len(news)} nyheter")

if __name__ == "__main__":
    main()
