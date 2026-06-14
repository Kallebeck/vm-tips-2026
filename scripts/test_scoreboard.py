import requests

URL = "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/scores-fixtures"

response = requests.get(
    URL,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30
)

print("STATUS:", response.status_code)
print("LENGTH:", len(response.text))
print("FIRST 1000 CHARS:")
print(response.text[:1000])
