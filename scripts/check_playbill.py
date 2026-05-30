import requests
from bs4 import BeautifulSoup
from pathlib import Path

URL = "https://playbill.com/shows/broadway"

response = requests.get(URL, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

shows = set()

for link in soup.find_all("a"):
    text = link.get_text(strip=True)
    if len(text) > 2:
        shows.add(text)

shows = sorted(shows)

output_file = Path("data/broadway_shows.txt")

old_shows = set()

if output_file.exists():
    old_shows = set(output_file.read_text().splitlines())

new_shows = set(shows)

added = sorted(new_shows - old_shows)

output_file.write_text("\n".join(shows))

if added:
    print("NEW SHOWS FOUND:")
    for show in added:
        print(show)

    Path("changes.txt").write_text(
        "New additions:\n\n" + "\n".join(added)
    )
else:
    print("No changes")
