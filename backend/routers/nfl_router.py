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

# Most recent completed regular season
CURRENT_COMPLETE_SEASON = 2025


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

        # Historical range
        for year in range(2002, CURRENT_COMPLETE_SEASON + 1):
            seasons.append(year)

        # Future / modern seasons (parquet or explicit support)
        CBS_SUPPORTED_YEARS = [2025]

        for year in range(CURRENT_COMPLETE_SEASON + 1, 2035):
            if parquet_exists(year) or year in CBS_SUPPORTED_YEARS:
                seasons.append(year)

        SEASON_CACHE["seasons"] = sorted(seasons)
        SEASON_CACHE["loaded"] = True


# ============================================================
# NFLVERSE WEEKLY HELPERS
# ============================================================
def nflverse_weekly_exists(season: int) -> bool:
    """
    Fast HEAD request to check if nflverse weekly parquet exists.
    """
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
    """
    Loads official nflverse weekly parquet for a season.
    """
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"stats_player/stats_player_{season}.parquet"
    )

    print(f"📡 Downloading nflverse weekly parquet: {url}")
    return pd.read_parquet(url)


# ============================================================
# ROSTER LOADER (nflverse parquet)
# ============================================================
def load_rosters(season: int) -> pd.DataFrame:
    """
    Loads official nflverse roster parquet for a season.
    Replaces the old nfl_data_py import_rosters() function.
    """
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"rosters/roster_{season}.parquet"
    )

    print(f"📡 Loading nflverse roster parquet for {season}")
    df = pd.read_parquet(url)

    # Normalize roster schema
    if "recent_team" in df.columns:
        df = df.rename(columns={"recent_team": "team"})

    return df


# ============================================================
# WEEKLY LOADER (Hybrid: nflverse → nfl_data_py → PBP)
# ============================================================
def load_weekly_data(season: int, week: int) -> pd.DataFrame:
    """
    Hybrid priority-based weekly loader:
    1. nflverse weekly parquet if published
    2. nfl_data_py weekly for completed seasons
    3. Custom PBP-derived weekly builder as last fallback
    """

    # ----------------------------
    # 1. nflverse official weekly parquet (if exists)
    # ----------------------------
    print(f"📥 Checking nflverse weekly parquet for {season}")
    if nflverse_weekly_exists(season):
        try:
            print(f"📡 Loading official nflverse weekly parquet for {season}")
            df = load_nflverse_weekly(season)

            if "week" in df.columns:
                df = df[df["week"] == week]

            rosters = load_rosters(season)
            df = harmonize_ids(df, rosters)

            return df

        except Exception as e:
            print(f"⚠️ nflverse parquet load failed for {season}: {e}")

    # ----------------------------
    # 2. nfl_data_py weekly for completed seasons
    # ----------------------------
    if season <= CURRENT_COMPLETE_SEASON:
        try:
            print(f"📥 Loading weekly data via nfl_data_py for {season}")

            from nfl_data_py import import_weekly_data

            # Try with explicit columns first
            try:
                weekly = import_weekly_data(
                    [season],
                    columns=[
                        "player_id",
                        "gsis_id",
                        "pfr_id",
                        "sportradar_id",
                        "espn_id",
                        "fantasy_id",
                        "player_name",
                        "recent_team",
                        "week",
                        "season",
                        "attempts",
                        "completions",
                        "passing_yards",
                        "passing_tds",
                        "interceptions",
                        "carries",
                        "rushing_yards",
                        "rushing_tds",
                        "receptions",
                        "targets",
                        "receiving_yards",
                        "receiving_tds",
                        "fantasy_points",
                        "fantasy_points_ppr",
                        "fantasy_points_half",
                    ],
                )
            except Exception as e:
                print(f"⚠️ Column-specific import failed, retrying with default schema: {e}")
                weekly = import_weekly_data([season])

            if "week" in weekly.columns:
                weekly = weekly[weekly["week"] == week]

            rosters = load_rosters(season)
            weekly = harmonize_ids(weekly, rosters)

            return weekly

        except Exception as e:
            print(f"⚠️ nfl_data_py weekly loader failed for {season}: {e}")

    # ----------------------------
    # 3. Custom PBP weekly builder as last fallback
    # ----------------------------
    print(f"📥 Falling back to custom PBP weekly builder for {season} week {week}")
    try:
        df = load_weekly_from_pbp(season, week)

        if df.empty:
            return df

        rosters = load_rosters(season)
        df = harmonize_ids(df, rosters)

        return df

    except Exception as e:
        print(f"⚠️ Custom PBP loader failed for {season} week {week}: {e}")
        return pd.DataFrame()


# ============================================================
# PLAYER USAGE ROUTE
# ============================================================
@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int, position: str = "ALL"):
    try:
        print(f"🔥 NFL ROUTE HIT: season={season}, week={week}, position={position}")

        df = load_weekly_data(season, week)

        print("📊 FULL DF SHAPE:", df.shape)

        if "week" not in df.columns:
            print("⚠️ No 'week' column found — returning empty")
            return []

        week_df = df[df["week"] == week]
        print("📅 WEEK DF SHAPE:", week_df.shape)

        if week_df.empty:
            return []

        # POSITION FILTERING (including WR/TE combo)
        pos = position.upper()

        if pos == "WR/TE":
            if "position" in week_df.columns:
                week_df = week_df[week_df["position"].isin(["WR", "TE"])]
        elif pos != "ALL":
            if "position" in week_df.columns:
                week_df = week_df[week_df["position"] == pos]

        print(f"🎯 FILTERED BY POSITION ({pos}) → {week_df.shape}")

        if week_df.empty:
            return []

        week_df = present_usage(week_df, pos)

        week_df = week_df.replace([np.inf, -np.inf], 0).fillna(0)

        return week_df.to_dict(orient="records")

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
