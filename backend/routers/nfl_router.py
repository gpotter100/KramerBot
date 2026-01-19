from fastapi import APIRouter, HTTPException
import pandas as pd
import numpy as np
import threading
from pathlib import Path

from services.presenters.usage_presenter import present_usage
from services.loaders.pbp_weekly_loader import load_weekly_from_pbp
from services.fantasy.scoring_engine import apply_scoring
from services.metrics.custom_metrics import add_efficiency_metrics
from services.snap_counts.loader import load_snap_counts

router = APIRouter()

# ============================================================
# GLOBAL SEASON CACHE (local parquet only)
# ============================================================

SEASON_CACHE = {"seasons": [], "loaded": False}
CACHE_LOCK = threading.Lock()

BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_PBP_DIR = BASE_DIR / "backend" / "data" / "pbp"



# ============================================================
# BUILD SEASON CACHE
# ============================================================

def build_season_cache():
    print("DEBUG: PBP FILES FOUND:", list(LOCAL_PBP_DIR.glob("pbp_*.parquet")))
    print("DEBUG: LOCAL_PBP_DIR =", LOCAL_PBP_DIR)

    with CACHE_LOCK:
        if SEASON_CACHE["loaded"]:
            return

        seasons = []
        for path in LOCAL_PBP_DIR.glob("pbp_*.parquet"):
            try:
                year = int(path.stem.split("_")[1])
                seasons.append(year)
            except Exception:
                continue

        SEASON_CACHE["seasons"] = sorted(seasons)
        SEASON_CACHE["loaded"] = True


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

    # Normalize columns
    df.columns = [c.lower() for c in df.columns]

    # Use recent_team as team
    if "recent_team" in df.columns:
        df = df.rename(columns={"recent_team": "team"})

    # Filter to active roster rows only
    if "status" in df.columns:
        df = df[df["status"].isin(["ACT", "PRA", "RES"])]

    # Drop rows with no player_id
    df = df[df["player_id"].notna()]

    # Deduplicate by player_id (keep most recent)
    df = df.sort_values("season", ascending=False).drop_duplicates("player_id")

    # Ensure position exists
    if "position" not in df.columns:
        df["position"] = None

    return df



# ============================================================
# UNIFIED WEEKLY LOADER
# ============================================================

def load_weekly_data(season: int, week: int) -> pd.DataFrame:
    from services.loaders.id_harmonizer import harmonize_ids  # avoid circular import

    print(f"🔥 Loading weekly data from local PBP for {season} week {week}")

    df = load_weekly_from_pbp(season, week)
    if df.empty:
        print(f"⚠️ No weekly data for {season} week {week}")
        return df

    # Harmonize IDs
    # Skip roster harmonization for future seasons (roster files incomplete)
    if season >= 2025:
        rosters = pd.DataFrame({"player_id": [], "player_name": [], "team": [], "position": []})
    
    else:
        rosters = load_rosters(season)

    df = harmonize_ids(df, rosters)

    print("DEBUG AFTER HARMONIZE:", df[["player_id", "player_name", "team", "position"]].head(20))

    # Snap counts
    # Skip snap counts for seasons where nflverse has no data
    if season >= 2025:
        snaps = pd.DataFrame({"player_id": [], "snap_pct": []})
    else:
    
        snaps = load_snap_counts(season, week)

    if not snaps.empty:
        # Normalize column names
        snaps.columns = [c.lower() for c in snaps.columns]
        
        # Use offense_pct as snap_pct (primary offensive usage)
        if "offense_pct" in snaps.columns:
            snaps = snaps.rename(columns={"offense_pct": "snap_pct"})
        else:
            # If no offense_pct exists, create a safe default
            snaps["snap_pct"] = 0

        # Merge safely
        df = df.merge(
            snaps[["player_id", "snap_pct"]],
            on="player_id",
            how="left"
        )

        df["snap_pct"] = df["snap_pct"].fillna(0)
    else:
        # No snap data at all
        df["snap_pct"] = 0

    print("DEBUG FINAL COLUMNS:", df.columns.tolist())

    return df


# ============================================================
# PLAYER USAGE ROUTE
# ============================================================

@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int, position: str = "ALL", scoring: str = "standard"):

    try:
        print(f"🔥 NFL ROUTE HIT: season={season}, week={week}, position={position}")

        df = load_weekly_data(season, week)
        if df.empty or "week" not in df.columns:
            return []

        week_df = df[df["week"] == week]
        if week_df.empty:
            return []

        pos = position.upper()

        if pos == "WR/TE":
            week_df = week_df[week_df["position"].isin(["WR", "TE"])]
        elif pos != "ALL":
            week_df = week_df[week_df["position"] == pos]

        if week_df.empty:
            return []

        # Present usage
        week_df = present_usage(week_df, pos)

        # Apply scoring
        week_df = apply_scoring(week_df, scoring)


        # Add advanced metrics
        week_df = add_efficiency_metrics(week_df)

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
