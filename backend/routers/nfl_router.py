from fastapi import APIRouter, HTTPException
import pandas as pd

router = APIRouter()

# ================================
# CUSTOM WEEKLY LOADER (2025+)
# ================================
def load_weekly_data(season: int) -> pd.DataFrame:
    """
    Loads weekly NFL player data.
    - Uses nfl_data_py for seasons <= 2024
    - Uses new nflverse parquet endpoint for 2025+
    """

    # Legacy seasons use nfl_data_py
    if season <= 2024:
        try:
            from nfl_data_py import import_weekly_data
            print(f"📥 Loading legacy weekly data via nfl_data_py for {season}")
            return import_weekly_data([season])
        except Exception as e:
            raise RuntimeError(f"Legacy loader failed for {season}: {e}")

    # New seasons use nflverse parquet
    url = f"https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_{season}.parquet"
    print(f"📥 Loading modern weekly data from {url}")

    try:
        df = pd.read_parquet(url)
        return df
    except Exception as e:
        raise RuntimeError(f"Modern loader failed for {season}: {e}")


# ================================
# NFL PLAYER USAGE ROUTE
# ================================
@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int):
    try:
        print(f"🔥 NFL ROUTE HIT: season={season}, week={week}")

        # Load data using patched loader
        df = load_weekly_data(season)
        print("📊 FULL DF SHAPE:", df.shape)

        # Filter to the requested week
        week_df = df[df["week"] == week]
        print("📅 WEEK DF SHAPE:", week_df.shape)

        if week_df.empty:
            return []

        # ================================
        # NORMALIZE COLUMN NAMES
        # ================================
        # Some parquet files use different casing or naming
        rename_map = {
            "recent_team": "team",
            "club": "team",
            "team_abbr": "team",
            "rush_attempt": "carries",
            "pass_attempt": "attempts",
        }

        week_df = week_df.rename(columns={k: v for k, v in rename_map.items() if k in week_df.columns})

        # Ensure required columns exist
        for col in ["team", "attempts", "receptions", "targets", "carries"]:
            if col not in week_df.columns:
                week_df[col] = 0

        # Snap % is not included in nflverse 2025+ weekly data
        if "snap_pct" not in week_df.columns:
            week_df["snap_pct"] = 0.0

        # ================================
        # AGGREGATE PLAYER USAGE
        # ================================
        usage = week_df.groupby("player_name").agg({
            "attempts": "sum",
            "receptions": "sum",
            "targets": "sum",
            "carries": "sum",
            "team": "first",
            "position": "first",
            "snap_pct": "mean",
            "passing_yards": "sum",
            "rushing_yards": "sum",
            "receiving_yards": "sum",
            "fantasy_points_ppr": "sum",        
        }).reset_index()

        print("📈 USAGE SHAPE:", usage.shape)

        # Sort by touches (attempts + receptions)
        usage["touches"] = usage["attempts"] + usage["receptions"]
        usage = usage.sort_values(by="touches", ascending=False)

        # Convert to JSON‑friendly dict
        return usage.to_dict(orient="records")

    except Exception as e:
        print("❌ ERROR IN NFL ROUTE:", e)
        raise HTTPException(status_code=500, detail=str(e))
