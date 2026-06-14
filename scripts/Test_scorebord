import requests
from bs4 import BeautifulSoup

URL = "https://www.espn.com/soccer/scoreboard/_/league/fifa.world"

response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
text = soup.get_text("\n")

lines = [line.strip() for line in text.splitlines() if line.strip()]

for line in lines[:300]:
    print(line)
