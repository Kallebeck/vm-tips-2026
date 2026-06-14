import requests

URL = "https://www.espn.com/soccer/scoreboard/_/league/fifa.world"

response = requests.get(
    URL,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)

print("STATUS:", response.status_code)
print("LENGTH:", len(response.text))
print("FIRST 1000 CHARS:")
print(response.text[:1000])
