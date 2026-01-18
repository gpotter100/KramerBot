from fastapi import APIRouter, HTTPException
import pandas as pd
import urllib.request
import threading
import numpy as np
import pkg_resources

from services.presenters.usage_presenter import present_usage
from services.loaders.pbp_weekly_loader import load_weekly_from_pbp
from services.loaders.id_harmonizer import harmonize_ids

print(">>> nfl_data_py VERSION:", pkg_resources.get_distribution("nfl_data_py").version)

router = APIRouter()

# ============================================================
# GLOBAL SEASON CACHE
# ============================================================
SEASON_CACHE = {
    "seasons": [],
    "loaded": False
}

CACHE_LOCK = threading.Lock()

# Most recent completed season (your system now supports 2025)
CURRENT_COMPLETE_SEASON = 2025


# ============================================================
# LIGHTWEIGHT PARQUET EXISTENCE CHECK
# ============================================================
def parquet_exists(year: int) -> bool:
    """
    HEAD request to check if nflverse weekly parquet exists.
    Used only for seasons AFTER 2025.
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
# BUILD SEASON CACHE
# ============================================================
def build_season_cache():
    """
    Builds the season list ONCE.
    Ensures 2025 is always included because you have local PBP data.
    """
    with CACHE_LOCK:
        if SEASON_CACHE["loaded"]:
            return

        seasons = []

        # Historical seasons
        for year in range(2002, CURRENT_COMPLETE_SEASON + 1):
            seasons.append(year)

        # Explicitly include 2025 (local PBP support)
        if 2025 not in seasons:
            seasons.append(2025)

        # Future seasons (2035 max)
        for year in range(CURRENT_COMPLETE_SEASON + 1, 2035):
            if parquet_exists(year):
                seasons.append(year)

        SEASON_CACHE["seasons"] = sorted(seasons)
        SEASON_CACHE["loaded"] = True


# ============================================================
# NFLVERSE WEEKLY HELPERS
# ============================================================
def nflverse_weekly_exists(season: int) -> bool:
    """
    HEAD check for nflverse weekly parquet.
    Disabled for 2025 because we use local PBP.
    """
    if season == 2025:
        return False

    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"stats_player/stats_player_{season}.parquet"
    )

    req = urllib.request.Request(url, method="HEAD")

    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


def load_nflverse_weekly(season: int) -> pd.DataFrame:
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"stats_player/stats_player_{season}.parquet"
    )
    print(f"📡 Loading nflverse weekly parquet for {season}")
    return pd.read_parquet(url)


# ============================================================
# ROSTER LOADER
# ============================================================
def load_rosters(season: int) -> pd.DataFrame:
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"rosters/roster_{season}.parquet"
    )

    print(f"📡 Loading nflverse roster parquet for {season}")
    df = pd.read_parquet(url)

    if "recent_team" in df.columns:
        df = df.rename(columns={"recent_team": "team"})

    return df


# ============================================================
# WEEKLY LOADER (2025-first logic)
# ============================================================
def load_weekly_data(season: int, week: int) -> pd.DataFrame:
    """
    Priority:
    1. 2025 → ALWAYS load from local PBP-derived weekly builder
    2. nflverse weekly parquet (if exists)
    3. nfl_data_py weekly (legacy seasons)
    4. PBP fallback
    """

    # ----------------------------
    # 1. 2025 → ALWAYS use local PBP weekly builder
    # ----------------------------
    if season == 2025:
        print(f"🔥 Loading 2025 weekly data from local PBP builder")
        df = load_weekly_from_pbp(season, week)

        if df.empty:
            return df

        rosters = load_rosters(season)
        df = harmonize_ids(df, rosters)
        return df

    # ----------------------------
    # 2. nflverse weekly parquet
    # ----------------------------
    if nflverse_weekly_exists(season):
        try:
            df = load_nflverse_weekly(season)
            if "week" in df.columns:
                df = df[df["week"] == week]

            rosters = load_rosters(season)
            df = harmonize_ids(df, rosters)
            return df

        except Exception as e:
            print(f"⚠️ nflverse weekly load failed: {e}")

    # ----------------------------
    # 3. nfl_data_py weekly (legacy)
    # ----------------------------
    if season <= CURRENT_COMPLETE_SEASON:
        try:
            from nfl_data_py import import_weekly_data

            try:
                weekly = import_weekly_data([season])
            except Exception:
                weekly = import_weekly_data([season])

            if "week" in weekly.columns:
                weekly = weekly[weekly["week"] == week]

            rosters = load_rosters(season)
            weekly = harmonize_ids(weekly, rosters)
            return weekly

        except Exception as e:
            print(f"⚠️ nfl_data_py weekly failed: {e}")

    # ----------------------------
    # 4. PBP fallback
    # ----------------------------
    print(f"📥 Falling back to PBP weekly builder for {season} week {week}")
    try:
        df = load_weekly_from_pbp(season, week)
        if df.empty:
            return df

        rosters = load_rosters(season)
        df = harmonize_ids(df, rosters)
        return df

    except Exception as e:
        print(f"⚠️ PBP fallback failed: {e}")
        return pd.DataFrame()


# ============================================================
# PLAYER USAGE ROUTE
# ============================================================
@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int, position: str = "ALL"):
    try:
        print(f"🔥 NFL ROUTE HIT: season={season}, week={week}, position={position}")

        df = load_weekly_data(season, week)

        if "week" not in df.columns:
            return []

        week_df = df[df["week"] == week]
        if week_df.empty:
            return []

        pos = position.upper()

        if pos == "WR/TE":
            if "position" in week_df.columns:
                week_df = week_df[week_df["position"].isin(["WR", "TE"])]
        elif pos != "ALL":
            if "position" in week_df.columns:
                week_df = week_df[week_df["position"] == pos]

        if week_df.empty:
            return []

        week_df = present_usage(week_df, pos)
        week_df = week_df.replace([np.inf, -np.inf], 0).fillna(0)

        return week_df.to_dict(orient="records")

    except Exception as e:
        print("❌ ERROR IN NFL ROUTE:", e)
        raise HTTPException(status_code=500, detail="Failed to load NFL data")


# ============================================================
# SEASONS ROUTE
# ============================================================
@router.get("/nfl/seasons")
def get_available_seasons():
    if not SEASON_CACHE["loaded"]:
        build_season_cache()

    return SEASON_CACHE["seasons"]
