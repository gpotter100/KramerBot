# backend/routers/nfl_router.py

from fastapi import APIRouter, HTTPException
from nfl_data_py import import_weekly_data
import pandas as pd

router = APIRouter()

@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int):
    try:
        print("🔥 NFL ROUTE HIT:", season, week)

        df = import_weekly_data([season])
        print("📊 FULL DF SHAPE:", df.shape)

        week_df = df[df["week"] == week]
        print("📅 WEEK DF SHAPE:", week_df.shape)

        usage = week_df.groupby("player_name").agg({
            "attempts": "sum",          # passing attempts
            "receptions": "sum",
            "targets": "sum",
            "carries": "sum",           # rushing attempts
            "recent_team": "first",     # team
            "position": "first"
        }).reset_index()

        print("📈 USAGE SHAPE:", usage.shape)

        usage = usage.sort_values(
            by=["attempts", "receptions", "targets"],
            ascending=False
        )

        return usage.to_dict(orient="records")

    except Exception as e:
        print("❌ ERROR IN NFL ROUTE:", e)
        raise HTTPException(status_code=500, detail=str(e))
