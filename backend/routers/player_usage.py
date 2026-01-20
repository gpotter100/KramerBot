from fastapi import APIRouter, HTTPException
from routers.nfl_router import load_weekly_data
from weekly.usage import aggregate_player_usage

router = APIRouter()


@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int):
    df = load_weekly_data(season, week)
    usage = aggregate_player_usage(df)
    return usage.to_dict(orient="records")

@router.get("/nfl/multi-usage/{season}")
def get_multi_week_usage(season: int, weeks: str, scoring: str = "standard"):
    """
    Aggregate player usage across multiple weeks.
    Example:
    /nfl/multi-usage/2025?weeks=1,2,3&scoring=standard
    """

    # Parse week list
    try:
        week_list = [int(w) for w in weeks.split(",") if w.strip()]
    except:
        raise HTTPException(status_code=400, detail="Invalid weeks parameter")

    if not week_list:
        raise HTTPException(status_code=400, detail="No weeks provided")

    all_rows = []

    # Load each week and aggregate raw rows
    for w in week_list:
        try:
            df = load_weekly_data(season, w)
            weekly_usage = aggregate_player_usage(df)
            rows = weekly_usage.to_dict(orient="records")
            all_rows.extend(rows)
        except Exception as e:
            print(f"Error loading week {w}: {e}")

    if not all_rows:
        return []

    # Aggregate across weeks
    aggregated = {}
    for row in all_rows:
        pid = row.get("player_id") or f"{row.get('player_name')}-{row.get('team')}"

        if pid not in aggregated:
            aggregated[pid] = {
                "player_id": pid,
                "player_name": row.get("player_name"),
                "team": row.get("team"),
                "position": row.get("position"),
                "weeks": [],
                "attempts": 0,
                "receptions": 0,
                "touches": 0,
                "total_yards": 0,
                "touchdowns": 0,
                "fantasy_points": 0,
                "fantasy_points_ppr": 0,
                "fantasy_points_half": 0,
                "fantasy_points_shen2000": 0,
            }

        agg = aggregated[pid]

        # Track contributing weeks
        if row.get("week") not in agg["weeks"]:
            agg["weeks"].append(row.get("week"))

        # Additive stats
        agg["attempts"] += row.get("attempts", 0)
        agg["receptions"] += row.get("receptions", 0)
        agg["touches"] += row.get("touches", 0)
        agg["total_yards"] += row.get("total_yards", 0)
        agg["touchdowns"] += row.get("touchdowns", 0)

        # Fantasy scoring
        agg["fantasy_points"] += row.get("fantasy_points", 0)
        agg["fantasy_points_ppr"] += row.get("fantasy_points_ppr", 0)
        agg["fantasy_points_half"] += row.get("fantasy_points_half", 0)
        agg["fantasy_points_shen2000"] += row.get("fantasy_points_shen2000", 0)

    # Convert dict → list
    result = list(aggregated.values())

    # Sort by fantasy points
    result.sort(key=lambda r: r.get("fantasy_points", 0), reverse=True)

    return result

