import requests
import pandas as pd
import json

ESPN_BASE = "https://site.web.api.espn.com/apis/site/v2/sports/football/nfl"


def _get_scoreboard(season: int, week: int) -> dict:
    """
    Fetch ESPN scoreboard for a given NFL week.
    """
    # ESPN uses dates, but also supports 'week' via params on some endpoints.
    # To keep it simple and robust, we use the scoreboard with 'week' and 'seasontype=2' (regular season).
    url = f"{ESPN_BASE}/scoreboard"
    params = {
        "week": week,
        "year": season,
        "seasontype": 2,  # 2 = regular season
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _get_game_summary(event_id: str) -> dict:
    url = f"{ESPN_BASE}/gamepackage"
    params = {"event": event_id}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    print("\n===== ESPN GAMEPACKAGE DEBUG =====")
    print(json.dumps(list(data.keys()), indent=2))
    print("==================================\n")

    return data



def _extract_player_rows_from_boxscore(summary_json: dict, season: int, week: int) -> list[dict]:
    """
    Parse ESPN summary JSON into per-player stat rows.
    We normalize into your existing schema as much as possible.
    """
    rows: list[dict] = []

    boxscore = summary_json.get("boxscore", {})
    teams = boxscore.get("teams", [])

    for team_entry in teams:
        team_info = team_entry.get("team", {})
        team_abbr = team_info.get("abbreviation")
        stats_groups = team_entry.get("statistics", [])

        # ESPN groups stats by category (passing, rushing, receiving, etc.)
        # Each group has 'athletes' with per-player stats.
        for group in stats_groups:
            athletes = group.get("athletes", [])
            for athlete in athletes:
                player = athlete.get("athlete", {})
                stats = athlete.get("stats", [])
                stat_labels = group.get("labels", [])

                player_name = player.get("displayName")
                position = player.get("position", {}).get("abbreviation")

                # Build a mapping of label -> value for this stat group
                stat_map = dict(zip(stat_labels, stats))

                # Initialize a base row
                row = {
                    "player_name": player_name,
                    "team": team_abbr,
                    "position": position,
                    "attempts": 0,
                    "receptions": 0,
                    "targets": 0,
                    "carries": 0,
                    "passing_yards": 0.0,
                    "rushing_yards": 0.0,
                    "receiving_yards": 0.0,
                    "fantasy_points": 0.0,
                    "fantasy_points_ppr": 0.0,
                    "passing_epa": 0.0,
                    "rushing_epa": 0.0,
                    "receiving_epa": 0.0,
                    "snap_pct": 0.0,
                    "week": week,
                    "season": season,
                }

                # Heuristics: map ESPN labels into your schema
                # These labels vary slightly but commonly include:
                # "CMP-ATT", "YDS", "CAR", "REC", "TGTS", etc.
                label_lower = [l.lower() for l in stat_labels]

                # Passing
                if "cmp-att" in label_lower or "cmp/att" in label_lower:
                    # We don't need completions, but attempts are useful
                    try:
                        idx = label_lower.index("cmp-att") if "cmp-att" in label_lower else label_lower.index("cmp/att")
                        cmp_att = stats[idx]
                        # Format like "23-35"
                        parts = cmp_att.split("-")
                        if len(parts) == 2:
                            row["attempts"] = int(parts[1])
                    except Exception:
                        pass

                if "yds" in label_lower and "passing" in group.get("name", "").lower():
                    try:
                        idx = label_lower.index("yds")
                        row["passing_yards"] = float(stats[idx])
                    except Exception:
                        pass

                # Rushing
                if "car" in label_lower:
                    try:
                        idx = label_lower.index("car")
                        row["carries"] = int(stats[idx])
                    except Exception:
                        pass

                if "yds" in label_lower and "rushing" in group.get("name", "").lower():
                    try:
                        idx = label_lower.index("yds")
                        row["rushing_yards"] = float(stats[idx])
                    except Exception:
                        pass

                # Receiving
                if "rec" in label_lower:
                    try:
                        idx = label_lower.index("rec")
                        row["receptions"] = int(stats[idx])
                    except Exception:
                        pass

                if "tgts" in label_lower or "tgt" in label_lower:
                    try:
                        idx = label_lower.index("tgts") if "tgts" in label_lower else label_lower.index("tgt")
                        row["targets"] = int(stats[idx])
                    except Exception:
                        pass

                if "yds" in label_lower and "receiving" in group.get("name", "").lower():
                    try:
                        idx = label_lower.index("yds")
                        row["receiving_yards"] = float(stats[idx])
                    except Exception:
                        pass

                # We can approximate fantasy points later in your route if needed.
                rows.append(row)

    return rows


def load_espn_weekly_data(season: int, week: int) -> pd.DataFrame:
    """
    High-level: fetch all games for a week, then aggregate player stats.
    Returns a pandas DataFrame matching your weekly usage schema as closely as possible.
    """
    try:
        print(f"📡 ESPN WEEKLY → Fetching scoreboard for {season} week {week}")
        scoreboard = _get_scoreboard(season, week)
    except Exception as e:
        print(f"❌ ESPN scoreboard request failed: {e}")
        return pd.DataFrame()

    events = scoreboard.get("events", [])
    if not events:
        print("⚠️ ESPN scoreboard returned no events")
        return pd.DataFrame()

    all_rows: list[dict] = []

    for event in events:
        event_id = event.get("id")
        if not event_id:
            continue

        try:
            print(f"📡 ESPN WEEKLY → Fetching summary for event {event_id}")
            summary = _get_game_summary(event_id)
            rows = _extract_player_rows_from_boxscore(summary, season, week)
            all_rows.extend(rows)
        except Exception as e:
            print(f"⚠️ ESPN summary fetch/parse failed for event {event_id}: {e}")
            continue

    df = pd.DataFrame(all_rows)
    print(f"📊 ESPN WEEKLY → Parsed {len(df)} player rows for {season} week {week}")
    return df
