import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests

QUERY = "fotbolls vm 2026 OR VM 2026 fotboll"
RSS_URL = f"https://news.google.com/rss/search?q={quote_plus(QUERY)}&hl=sv&gl=SE&ceid=SE:sv"
OUTPUT_FILE = "nyheter.json"

def clean(text):
    text = re.sub(r"<[^>]+>", "", text or "")
    return " ".join(text.split())

def main():
    response = requests.get(
        RSS_URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items = root.findall(".//item")

    news = []

    for item in items[:10]:
        title = clean(item.findtext("title"))
        link = clean(item.findtext("link"))
        description = clean(item.findtext("description"))
        pub_date_raw = item.findtext("pubDate") or ""

        published = ""
        try:
            published = parsedate_to_datetime(pub_date_raw).strftime("%Y-%m-%d %H:%M")
        except Exception:
            published = pub_date_raw

        news.append({
            "title": title,
            "source": "Google News",
            "published": published,
            "summary": description[:220],
            "url": link
        })

    if not news:
        news = [{
            "title": "Inga VM-nyheter hittades just nu",
            "source": "Google News",
            "published": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "summary": "Flödet kontrollerades men inga nyheter hittades just nu.",
            "url": "https://news.google.com/"
        }]

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(news, f, ensure_ascii=False, indent=2)

    print(f"Skapade {OUTPUT_FILE} med {len(news)} nyheter")

if __name__ == "__main__":
    main()
