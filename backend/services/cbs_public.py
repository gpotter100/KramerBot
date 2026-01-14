# backend/services/cbs_public.py

import html
import os
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup

LEAGUE_BASE_URL = os.getenv("LEAGUE_BASE_URL", "").rstrip("/")


class LeagueDataError(Exception):
    pass


import httpx

async def fetch_html(path: str) -> str:
    base_url = os.getenv("LEAGUE_BASE_URL")
    if not base_url:
        raise LeagueDataError("LEAGUE_BASE_URL is not configured")

    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/143.0.0.0 Safari/537.36"
        ),
        "Cookie": "QSI_History_Session=https%3A%2F%2Flouieshades.football.cbssports.com%2F%3Flogin%3Dconfirmed%26tid%3D1768358797~1768358801836%7Chttps%3A%2F%2Flouieshades.football.cbssports.com%2Fhome~1768358814281%7Chttps%3A%2F%2Flouieshades.football.cbssports.com%2Fstandings%2Foverall~1768359022019"
    }

    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        resp = await client.get(url)
        if resp.status_code != 200:
            raise LeagueDataError(f"Failed to fetch {url} (status {resp.status_code})")
        return resp.text



async def get_standings() -> List[Dict[str, Any]]:
    try:
        html = await fetch_html("standings")
        print("DEBUG CBS HTML START")
        print(html[:2000])
        print("DEBUG CBS HTML END")
    except Exception as e:
        print("FETCH ERROR:", str(e))
        raise LeagueDataError(f"Fetch failed: {str(e)}")

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        raise LeagueDataError("Could not find standings table")

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

