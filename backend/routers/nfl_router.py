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
from services.metrics.fantasy_attribution import compute_fantasy_attribution

router = APIRouter()

# ============================================================
# GLOBAL SEASON CACHE
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
# ROSTER LOADER (PATCHED)
# ============================================================

def load_rosters(season: int) -> pd.DataFrame:
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"rosters/roster_{season}.parquet"
    )

    print(f"📡 Loading nflverse roster parquet for {season}")
    df = pd.read_parquet(url)

    df.columns = [c.lower() for c in df.columns]

    # Fallback: nflverse 2025+ sometimes uses gsis_id or nfl_id
    if "player_id" not in df.columns:
        print("⚠️ roster file missing player_id — attempting fallback ID mapping")

        if "gsis_id" in df.columns:
            df = df.rename(columns={"gsis_id": "player_id"})
        elif "nfl_id" in df.columns:
            df = df.rename(columns={"nfl_id": "player_id"})
        else:
            print("❌ No usable ID column found — returning empty roster")
            return pd.DataFrame({"player_id": [], "player_name": [], "team": [], "position": []})

    if "recent_team" in df.columns:
        df = df.rename(columns={"recent_team": "team"})

    if "status" in df.columns:
        df = df[df["status"].isin(["ACT", "PRA", "RES"])]

    df = df.sort_values("season", ascending=False).drop_duplicates("player_id")

    if "position" not in df.columns:
        df["position"] = None

    return df


# ============================================================
# WEEKLY LOADER (PATCHED)
# ============================================================

def load_weekly_data(season: int, week: int) -> pd.DataFrame:
    from services.loaders.id_harmonizer import harmonize_ids

    print(f"🔥 Loading weekly data from local PBP for {season} week {week}")

    df = load_weekly_from_pbp(season, week)
    if df.empty:
        print(f"⚠️ No weekly data for {season} week {week}")
        return df

    # Load rosters
    try:
        rosters = load_rosters(season)
        print(f"📘 Loaded roster rows: {len(rosters)} for season {season}")
    except Exception as e:
        print(f"⚠️ Failed to load rosters for {season}: {e}")
        rosters = pd.DataFrame({"player_id": [], "player_name": [], "team": [], "position": []})

    # Harmonize IDs
    df = harmonize_ids(df, rosters)

    try:
        print("DEBUG AFTER HARMONIZE (first 10 rows):")
        print(df[["player_id", "player_name", "team", "position"]].head(10))
    except Exception:
        print("⚠️ DEBUG: position column missing after harmonize_ids")

    # Snap counts
    if season >= 2025:
        snaps = pd.DataFrame({"player_id": [], "snap_pct": []})
    else:
        snaps = load_snap_counts(season, week)

    if not snaps.empty:
        snaps.columns = [c.lower() for c in snaps.columns]

        if "offense_pct" in snaps.columns:
            snaps = snaps.rename(columns={"offense_pct": "snap_pct"})
        else:
            snaps["snap_pct"] = 0

        df = df.merge(
            snaps[["player_id", "snap_pct"]],
            on="player_id",
            how="left"
        )
        df["snap_pct"] = df["snap_pct"].fillna(0)
    else:
        df["snap_pct"] = 0

    return df


# ============================================================
# WEEKLY PLAYER USAGE ROUTE (PATCHED)
# ============================================================

@router.get("/nfl/player-usage/{season}/{week}")
def get_player_usage(season: int, week: int, position: str = "ALL", scoring: str = "standard"):

    try:
        print(f"🔥 NFL ROUTE HIT: season={season}, week={week}, position={position}, scoring={scoring}")

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

        # Apply scoring (all systems) + select active
        week_df = apply_scoring(week_df, scoring)

        # Fantasy attribution
        week_df = compute_fantasy_attribution(week_df, scoring)

        # Present usage last
        week_df = present_usage(week_df, pos)

        # Advanced metrics
        week_df = add_efficiency_metrics(week_df)

        week_df = week_df.replace([np.inf, -np.inf], 0).fillna(0)

        return week_df.to_dict(orient="records")

    except Exception as e:
        import traceback
        print("❌ ERROR IN NFL ROUTE:", e)
        traceback.print_exc()   # <— THIS is the important part
        raise HTTPException(status_code=500, detail="Failed to load NFL data")



# ============================================================
# MULTI-WEEK USAGE + ATTRIBUTION (PATCHED)
# ============================================================

@router.get("/nfl/multi-usage-v2/{season}")
def get_multi_week_usage(season: int, weeks: str, position: str = "ALL", scoring: str = "standard"):

    try:
        week_list = [int(w) for w in weeks.split(",") if w.strip()]
        if not week_list:
            raise HTTPException(status_code=400, detail="No weeks provided")

        pos = position.upper()
        all_frames = []

        for w in week_list:
            df = load_weekly_data(season, w)
            if df.empty or "week" not in df.columns:
                continue

            week_df = df[df["week"] == w]
            if week_df.empty:
                continue

            if pos == "WR/TE":
                week_df = week_df[week_df["position"].isin(["WR", "TE"])]
            elif pos != "ALL":
                week_df = week_df[week_df["position"] == pos]

            if week_df.empty:
                continue

            week_df = week_df.replace([np.inf, -np.inf], 0).fillna(0)
            week_df["week"] = w

            all_frames.append(week_df)

        if not all_frames:
            return []

        df_all = pd.concat(all_frames, ignore_index=True)

        required_cols = [
            "attempts", "receptions",
            "passing_yards", "rushing_yards", "receiving_yards",
            "passing_tds", "rushing_tds", "receiving_tds",
            "interceptions", "fumbles_lost"
        ]
        for col in required_cols:
            if col not in df_all.columns:
                df_all[col] = 0

        group_cols = ["player_id", "player_name", "team", "position"]

        agg_df = (
            df_all.groupby(group_cols, dropna=False)
            .agg(
                attempts=("attempts", "sum"),
                receptions=("receptions", "sum"),
                passing_yards=("passing_yards", "sum"),
                rushing_yards=("rushing_yards", "sum"),
                receiving_yards=("receiving_yards", "sum"),
                passing_tds=("passing_tds", "sum"),
                rushing_tds=("rushing_tds", "sum"),
                receiving_tds=("receiving_tds", "sum"),
                interceptions=("interceptions", "sum"),
                fumbles_lost=("fumbles_lost", "sum"),
            )
            .reset_index()
        )

        agg_df["touches"] = agg_df["attempts"] + agg_df["receptions"]
        agg_df["total_yards"] = (
            agg_df["passing_yards"]
            + agg_df["rushing_yards"]
            + agg_df["receiving_yards"]
        )
        agg_df["touchdowns"] = (
            agg_df["passing_tds"]
            + agg_df["rushing_tds"]
            + agg_df["receiving_tds"]
        )

        agg_df = apply_scoring(agg_df, scoring)
        agg_df = compute_fantasy_attribution(agg_df, scoring)
        agg_df = present_usage(agg_df, pos)

        agg_df = agg_df.replace([np.inf, -np.inf], 0).fillna(0)
        agg_df = agg_df.sort_values("fantasy_points", ascending=False)

        return agg_df.to_dict(orient="records")

    except Exception as e:
        print("❌ ERROR IN MULTI-WEEK NFL ROUTE:", e)
        raise HTTPException(status_code=500, detail="Failed to load multi-week NFL data")


# ============================================================
# SEASONS ROUTE
# ============================================================

@router.get("/nfl/seasons")
def get_available_seasons():
    if not SEASON_CACHE["loaded"]:
        build_season_cache()
    return SEASON_CACHE["seasons"]
