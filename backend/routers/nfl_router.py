from turtle import pos
from fastapi import APIRouter, HTTPException
from .cbs_fallback import load_cbs_weekly_data
from services.espn_weekly_loader import load_espn_weekly_data
from services.presenters.usage_presenter import present_usage
from services.loaders.pbp_weekly_loader import load_weekly_from_pbp
import pandas as pd
import urllib.error
import urllib.request
import threading

router = APIRouter()

# ============================================================
# GLOBAL SEASON CACHE
# ============================================================
SEASON_CACHE = {
    "seasons": [],
    "loaded": False
}

CACHE_LOCK = threading.Lock()


# ============================================================
# LIGHTWEIGHT PARQUET EXISTENCE CHECK (HEAD request)
# ============================================================
def parquet_exists(year: int) -> bool:
    """
    Fast HEAD request to check if a parquet file exists.
    Avoids downloading or loading full data.
    """
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"stats_player/stats_player_{year}.parquet"
    )

    req = urllib.request.Request(url, method="HEAD")

    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


# ============================================================
# BUILD SEASON CACHE ONCE
# ============================================================
def build_season_cache():
    """
    Builds the season list ONCE at startup or first request.
    Uses lightweight checks only.
    """
    with CACHE_LOCK:
        if SEASON_CACHE["loaded"]:
            return

        seasons = []

        # Known historical range for nfl_data_py
        for year in range(2002, 2025):
            seasons.append(year)

        # Modern seasons (2025+)
        CBS_SUPPORTED_YEARS = [2025]

        for year in range(2025, 2035):
            if parquet_exists(year) or year in CBS_SUPPORTED_YEARS:
                seasons.append(year)

        SEASON_CACHE["seasons"] = sorted(seasons)
        SEASON_CACHE["loaded"] = True


# ============================================================
# WEEKLY LOADER (Legacy 2002–2024, PBP-Derived 2025+)
# ============================================================
from services.loaders.pbp_weekly_loader import load_weekly_from_pbp

def load_weekly_data(season: int, week: int) -> pd.DataFrame:
    """
    Loads weekly NFL player data.
    - Uses nfl_data_py for seasons <= 2024
    - Uses PBP-derived weekly stats for 2025+
    """

    # ----------------------------
    # Legacy seasons (2002–2024)
    # ----------------------------
    if season <= 2024:
        try:
            from nfl_data_py import import_weekly_data
            print(f"📥 Loading legacy weekly data via nfl_data_py for {season}")
            return import_weekly_data([season])
        except Exception as e:
            print(f"⚠️ Legacy loader failed for {season}: {e}")
            return pd.DataFrame()

    # ----------------------------
    # Modern seasons (2025+ via PBP)
    # ----------------------------
    print(f"📥 Loading modern weekly data via PBP for {season} week {week}")
    df = load_weekly_from_pbp(season, week)
    return df

# ============================================================
# PLAYER USAGE ROUTE
# ============================================================
from services.presenters.usage_presenter import present_usage

@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int, position: str = "ALL"):
    try:
        print(f"🔥 NFL ROUTE HIT: season={season}, week={week}, position={position}")

        # Load weekly data (legacy or PBP)
        df = load_weekly_data(season, week)

        print("📊 FULL DF SHAPE:", df.shape)

        # Ensure week column exists
        if "week" not in df.columns:
            print("⚠️ No 'week' column found — returning empty")
            return []

        # Filter to requested week
        week_df = df[df["week"] == week]
        print("📅 WEEK DF SHAPE:", week_df.shape)

        if week_df.empty:
            return []

        # ============================================================
        # POSITION FILTERING (including WR/TE combo)
        # ============================================================
        pos = position.upper()

        if pos == "WR/TE":
            week_df = week_df[week_df["position"].isin(["WR", "TE"])]
        elif pos != "ALL":
            week_df = week_df[week_df["position"] == pos]

        print(f"🎯 FILTERED BY POSITION ({pos}) → {week_df.shape}")

        if week_df.empty:
            return []

        # ============================================================
        # PRESENTATION LAYER
        # ============================================================
        week_df = present_usage(week_df, pos)

        # ============================================================
        # CLEAN INVALID FLOATS FOR JSON
        # ============================================================
        import numpy as np
        week_df = week_df.replace([np.inf, -np.inf], 0).fillna(0)

        return week_df.to_dict(orient="records")

        # ============================================================
        # NORMALIZE COLUMN NAMES
        # ============================================================
        rename_map = {
            "recent_team": "team",
            "club": "team",
            "team_abbr": "team",
            "rush_attempt": "carries",
            "pass_attempt": "attempts",
        }

        # Apply renames first
        week_df = week_df.rename(
            columns={k: v for k, v in rename_map.items() if k in week_df.columns}
        )

        # Ensure receptions exists BEFORE calculating 0.5 PPR
        if "receptions" not in week_df.columns:
            week_df["receptions"] = 0

        # Create 0.5 PPR fantasy scoring
        week_df["fantasy_points_0.5ppr"] = (
            week_df.get("fantasy_points", 0) + 0.5 * week_df.get("receptions", 0)
        )

        # Ensure required columns exist
        required_cols = [
            "team", "attempts", "receptions", "targets", "carries",
            "passing_yards", "rushing_yards", "receiving_yards",
            "fantasy_points", "fantasy_points_ppr", "fantasy_points_0.5ppr",
            "passing_epa", "rushing_epa", "receiving_epa"
        ]

        for col in required_cols:
            if col not in week_df.columns:
                week_df[col] = 0

        # Snap percentage fallback
        if "snap_pct" not in week_df.columns:
            week_df["snap_pct"] = 0.0

        # ============================================================
        # AGGREGATE PLAYER USAGE
        # ============================================================
        usage = (
            week_df
            .groupby("player_name", as_index=False)
            .agg({
                # Passing
                "attempts": "sum",
                "completions": "sum",
                "passing_yards": "sum",
                "passing_tds": "sum",
                "interceptions": "sum",
                "passing_air_yards": "sum",
                "passing_first_downs": "sum",
                "passing_epa": "sum",
                # Rushing
                "carries": "sum",
                "rushing_yards": "sum",
                "rushing_tds": "sum",
                "rushing_fumbles": "sum",
                "rushing_fumbles_lost": "sum",
                "rushing_first_downs": "sum",
                "rushing_epa": "sum",
                # Receiving
                "receptions": "sum",
                "targets": "sum",
                "receiving_yards": "sum",
                "receiving_tds": "sum",
                "receiving_air_yards": "sum",
                "receiving_first_downs": "sum",
                "receiving_epa": "sum",
                # Fantasy
                "fantasy_points": "sum",
                "fantasy_points_ppr": "sum",
                "fantasy_points_0.5ppr": "sum",
                # Meta
                "team": "first",
                "position": "first",
                "snap_pct": "mean",
            })
        )


        usage["touches"] = usage["attempts"] + usage["receptions"]
        usage = usage.sort_values(by="touches", ascending=False)

        print("📈 USAGE SHAPE:", usage.shape)
        return usage.fillna(0).to_dict(orient="records")

    except Exception as e:
        print("❌ ERROR IN NFL ROUTE:", e)
        raise HTTPException(status_code=500, detail="Failed to load NFL data")


# ============================================================
# OPTIMIZED, CACHED SEASONS ROUTE
# ============================================================
@router.get("/nfl/seasons")
def get_available_seasons():
    """
    Returns cached seasons instantly.
    If cache is empty, builds it once.
    """
    if not SEASON_CACHE["loaded"]:
        build_season_cache()

    return SEASON_CACHE["seasons"]
