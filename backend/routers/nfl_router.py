from fastapi import APIRouter, HTTPException
from cbs_fallback import load_cbs_weekly_data
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
        CBS_SUPPORTED_YEARS = [2025]  # CBS fallback supports these even without parquet

        for year in range(2025, 2035):
            if parquet_exists(year) or year in CBS_SUPPORTED_YEARS:
                seasons.append(year)


        SEASON_CACHE["seasons"] = sorted(seasons)
        SEASON_CACHE["loaded"] = True


# ============================================================
# WEEKLY LOADER (Legacy 2002–2024, Modern 2025+)
# ============================================================
def load_weekly_data(season: int) -> pd.DataFrame:
    """
    Loads weekly NFL player data.
    - Uses nfl_data_py for seasons <= 2024
    - Uses nflverse parquet for 2025+
    - Returns empty DataFrame if data is unavailable
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
    # Modern seasons (2025+)
    # ----------------------------
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"stats_player/stats_player_{season}.parquet"
    )
    print(f"📥 Attempting modern weekly data from {url}")

    try:
        return pd.read_parquet(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"⚠️ No nflverse data published yet for {season}")
            return pd.DataFrame()
        print(f"⚠️ Modern loader HTTP error for {season}: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"⚠️ Modern loader error for {season}: {e}")
        return pd.DataFrame()


# ============================================================
# PLAYER USAGE ROUTE
# ============================================================
@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int):
    try:
        print(f"🔥 NFL ROUTE HIT: season={season}, week={week}")

        df = load_weekly_data(season)

        if df.empty and season >= 2025:
            print("🔄 Falling back to CBS public league data...")
            df = load_cbs_weekly_data(season, week)

        print("📊 FULL DF SHAPE:", df.shape)

        # Filter to requested week
        week_df = df[df["week"] == week]
        print("📅 WEEK DF SHAPE:", week_df.shape)

        if week_df.empty:
            return []

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

        week_df = week_df.rename(
            columns={k: v for k, v in rename_map.items() if k in week_df.columns}
        )

        required_cols = [
            "team", "attempts", "receptions", "targets", "carries",
            "passing_yards", "rushing_yards", "receiving_yards",
            "fantasy_points", "fantasy_points_ppr",
            "passing_epa", "rushing_epa", "receiving_epa"
        ]

        for col in required_cols:
            if col not in week_df.columns:
                week_df[col] = 0

        if "snap_pct" not in week_df.columns:
            week_df["snap_pct"] = 0.0

        # ============================================================
        # AGGREGATE PLAYER USAGE
        # ============================================================
        usage = (
            week_df
            .groupby("player_name", as_index=False)
            .agg({
                "attempts": "sum",
                "receptions": "sum",
                "targets": "sum",
                "carries": "sum",
                "passing_yards": "sum",
                "rushing_yards": "sum",
                "receiving_yards": "sum",
                "fantasy_points": "sum",
                "fantasy_points_ppr": "sum",
                "team": "first",
                "position": "first",
                "snap_pct": "mean",
                "passing_epa": "sum",
                "rushing_epa": "sum",
                "receiving_epa": "sum"
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
