from fastapi import APIRouter, HTTPException
from weekly.loader import load_weekly_data, load_weekly_pbp
from weekly.usage import aggregate_player_usage
from analytics.attribution_engine import compute_multiweek_attribution

router = APIRouter()

@router.get("/nfl/multi-attribution/{season}")
def get_multiweek_attribution(season: int, weeks: str, scoring: str = "standard"):
    week_list = [int(w) for w in weeks.split(",") if w.strip()]

    usage_rows = []
    pbp_rows = []

    for w in week_list:
        df_usage = load_weekly_data(season, w)
        usage = aggregate_player_usage(df_usage)
        usage_rows.extend(usage.to_dict(orient="records"))

        df_pbp = load_weekly_pbp(season, w)
        pbp_rows.extend(df_pbp.to_dict(orient="records"))

    return compute_multiweek_attribution(pbp_rows, usage_rows)

def compute_multiweek_attribution(pbp_rows, usage_rows): ...
