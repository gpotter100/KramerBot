# backend/services/cbs_public.py

import html
import os
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup

LEAGUE_BASE_URL = os.getenv("LEAGUE_BASE_URL", "").rstrip("/")


class LeagueDataError(Exception):
    pass


async def fetch_html(path: str) -> str:
    if not LEAGUE_BASE_URL:
        raise LeagueDataError("LEAGUE_BASE_URL is not configured")

    url = f"{LEAGUE_BASE_URL}/{path.lstrip('/')}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise LeagueDataError(f"Failed to fetch {url} (status {resp.status_code})")
        return resp.text


async def get_standings() -> List[Dict[str, Any]]:
    html = await fetch_html("standings")

    with open("/tmp/cbs_debug.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("DEBUG CBS HTML START")
    print(html[:2000])
    print("DEBUG CBS HTML END")

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")
    if not table:
        raise LeagueDataError("Could not find standings table")

    # CBS HTML may change; this is intentionally defensive and simple
    standings: List[Dict[str, Any]] = []
    rows = table.tbody.find_all("tr") if table.tbody else table.find_all("tr")[1:]

    rank = 1
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        team_cell = cells[0]
        record_cell = cells[1]
        pf_cell = cells[2]
        pa_cell = cells[3]
        streak_cell = cells[4]

        team_name = (team_cell.get_text(strip=True) or "").replace("\xa0", " ")
        record_text = record_cell.get_text(strip=True)
        points_for_text = pf_cell.get_text(strip=True)
        points_against_text = pa_cell.get_text(strip=True)
        streak = streak_cell.get_text(strip=True)

        wins = losses = ties = 0
        if record_text:
            parts = record_text.split("-")
            try:
                if len(parts) >= 2:
                    wins = int(parts[0])
                    losses = int(parts[1])
                if len(parts) == 3:
                    ties = int(parts[2])
            except ValueError:
                pass

        def parse_float(val: str) -> float:
            try:
                return float(val.replace(",", ""))
            except ValueError:
                return 0.0

        standings.append({
            "rank": rank,
            "team_name": team_name,
            "wins": wins,
            "losses": losses,
            "ties": ties,
            "points_for": parse_float(points_for_text),
            "points_against": parse_float(points_against_text),
            "streak": streak,
        })
        rank += 1

    if not standings:
        raise LeagueDataError("No standings rows parsed")

    return standings
