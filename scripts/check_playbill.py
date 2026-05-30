import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re
import time

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

# Words that appear in nav, footer, ads — never show titles
JUNK_PATTERNS = re.compile(
    r'^(broadway|off.broadway|upcoming|london|shows|tony|playbill|home|'
    r'search|tickets|news|menu|login|sign|subscribe|advertise|contact|'
    r'about|privacy|terms|copyright|all rights|follow us|newsletter|'
    r'buy tickets|learn more|see more|view all|get tickets|find tickets|'
    r'back to|close|open|toggle|skip|share|facebook|twitter|instagram|'
    r'youtube|tiktok|shop|store|donate|support|sponsor|partner)$',
    re.IGNORECASE
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def extract_shows(html: str) -> set:
    soup = BeautifulSoup(html, "html.parser")
    shows = set()

    # Strategy 1: Look for links whose href contains /production/
    # Playbill uses URLs like /production/hamilton-richard-rodgers-theatre-vault-...
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/production/" in href:
            text = a.get_text(strip=True)
            if text and len(text) > 2:
                shows.add(text)

    # Strategy 2: Look for article/card elements with show titles
    # Playbill wraps each show in a card — grab the heading text inside
    for el in soup.select("article h2, article h3, .show-card h2, .show-card h3, "
                          ".production-card h2, .production-card h3, "
                          "[class*='show'] h2, [class*='show'] h3, "
                          "[class*='production'] h2, [class*='production'] h3"):
        text = el.get_text(strip=True)
        if text and len(text) > 2:
            shows.add(text)

    # Filter out obvious junk
    cleaned = set()
    for show in shows:
        # Skip single words that are likely nav items
        if JUNK_PATTERNS.match(show):
            continue
        # Skip things that look like dates, numbers, or URLs
        if re.match(r'^[\d\s/\-\.]+$', show):
            continue
        if 'http' in show.lower():
            continue
        # Skip very long strings (likely ad copy or descriptions, not titles)
        if len(show) > 80:
            continue
        cleaned.add(show)

    return cleaned


changes = []

for category, (url, filename) in PAGES.items():
    print(f"Checking {category}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        continue

    shows = extract_shows(response.text)
    print(f"  Found {len(shows)} productions")

    file_path = Path(filename)
    previous = set()
    if file_path.exists():
        content = file_path.read_text().strip()
        if content:
            previous = set(content.splitlines())

    added = sorted(shows - previous)

    # Write the updated snapshot (union of old + new, since we ignore removals)
    updated = previous | shows
    file_path.write_text("\n".join(sorted(updated)))

    if added:
        changes.append(f"\n### {category}\n")
        for show in added:
            changes.append(f"- {show}")
        print(f"  New: {added}")
    else:
        print(f"  No new productions.")

    time.sleep(2)  # Be polite to Playbill's servers between requests

if changes:
    Path("changes.txt").write_text(
        "## 🎭 New Productions Detected\n\n" +
        "\n".join(changes) +
        "\n"
    )
    print("changes.txt written.")
else:
    print("No changes. No issue will be created.")
