from fastapi import APIRouter
from weekly.loader import load_weekly_data
from weekly.usage import aggregate_player_usage

router = APIRouter()


@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int):
    df = load_weekly_data(season, week)
    usage = aggregate_player_usage(df)
    return usage.to_dict(orient="records")
