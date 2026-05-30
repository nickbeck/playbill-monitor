import requests
from bs4 import BeautifulSoup
from pathlib import Path

PAGES = {
    "Broadway": (
        "https://playbill.com/shows/broadway",
        "data/broadway.txt"
    ),
    "Upcoming Broadway": (
        "https://playbill.com/shows/upcoming-broadway",
        "data/upcoming_broadway.txt"
    ),
    "Off-Broadway": (
        "https://playbill.com/shows/offbroadway",
        "data/offbroadway.txt"
    ),
    "London": (
        "https://playbill.com/shows/london",
        "data/london.txt"
    ),
}

changes = []

for category, (url, filename) in PAGES.items():

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    shows = set()

    for link in soup.find_all("a"):
        text = link.get_text(strip=True)

        if len(text) > 3:
            shows.add(text)

    current = sorted(shows)

    file_path = Path(filename)

    previous = set()

    if file_path.exists():
        previous = set(file_path.read_text().splitlines())

    added = sorted(set(current) - previous)

    file_path.write_text("\n".join(current))

    if added:
        changes.append(f"\n{category}\n")
        for show in added:
            changes.append(f"+ {show}")

if changes:
    Path("changes.txt").write_text(
        "🎭 New Productions Added\n\n" +
        "\n".join(changes)
    )
