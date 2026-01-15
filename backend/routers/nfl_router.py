# backend/routers/nfl_router.py

from fastapi import APIRouter, HTTPException
from nfl_data_py import import_weekly_data
import pandas as pd

router = APIRouter()

@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int):
    try:
        df = import_weekly_data([season])
        week_df = df[df["week"] == week]

        usage = week_df.groupby("player_name").agg({
            "attempts": "sum",
            "receptions": "sum",
            "targets": "sum",
            "carries": "sum",
            "rush_attempt": "sum",
            "pass_attempt": "sum",
            "snap_pct": "mean",
            "team": "first",
            "position": "first"
        }).reset_index()

        usage = usage.sort_values(by=["attempts", "receptions", "targets"], ascending=False)
        return usage.to_dict(orient="records")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
