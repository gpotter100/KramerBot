import pandas as pd
import requests
from bs4 import BeautifulSoup

# ============================================================
# CBS PUBLIC LEAGUE FALLBACK SCRAPER
# ============================================================

CBS_LEAGUE_URL = (
    "https://www.cbssports.com/fantasy/football/stats/"
    "playersort/overall/avg/standard/"
    "{season}/{week}/"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}


def load_cbs_weekly_data(season: int, week: int) -> pd.DataFrame:
    """
    Scrapes CBS public fantasy stats for a given season/week.
    Returns a DataFrame matching the nflverse schema.
    """

    url = CBS_LEAGUE_URL.format(season=season, week=week)
    print(f"📡 CBS FALLBACK → Fetching: {url}")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ CBS request failed: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(resp.text, "html.parser")

    # CBS tables use <table class="TableBase-table">
    table = soup.find("table", class_="TableBase-table")
    if not table:
        print("⚠️ CBS table not found")
        return pd.DataFrame()

    rows = table.find_all("tr")
    if not rows:
        print("⚠️ CBS rows not found")
        return pd.DataFrame()

    parsed = []

    for row in rows[1:]:  # skip header
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 8:
            continue

        # CBS columns vary slightly year to year, but typically:
        # 0 = Player
        # 1 = Team
        # 2 = Position
        # 3 = Passing Yards
        # 4 = Rushing Yards
        # 5 = Receiving Yards
        # 6 = Fantasy Points
        # 7 = Fantasy Points PPR (if available)

        try:
            player_name = cols[0]
            team = cols[1]
            position = cols[2]

            passing_yards = float(cols[3] or 0)
            rushing_yards = float(cols[4] or 0)
            receiving_yards = float(cols[5] or 0)
            fantasy_points = float(cols[6] or 0)
            fantasy_points_ppr = float(cols[7] or fantasy_points)

            # CBS does not provide attempts/targets/snap_pct
            # We fill these with zeros for schema compatibility.
            parsed.append({
                "player_name": player_name,
                "team": team,
                "position": position,
                "attempts": 0,
                "receptions": 0,
                "targets": 0,
                "carries": 0,
                "passing_yards": passing_yards,
                "rushing_yards": rushing_yards,
                "receiving_yards": receiving_yards,
                "fantasy_points": fantasy_points,
                "fantasy_points_ppr": fantasy_points_ppr,
                "passing_epa": 0,
                "rushing_epa": 0,
                "receiving_epa": 0,
                "snap_pct": 0.0,
                "week": week,
            })

        except Exception as e:
            print(f"⚠️ CBS row parse error: {e}")
            continue

    df = pd.DataFrame(parsed)
    print(f"📊 CBS FALLBACK → Parsed {len(df)} players")

    return df
