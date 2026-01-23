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

    # Fallback: nflverse 2025+ sometimes uses gsis_id or nfl_id instead of player_id
    if "player_id" not in df.columns:
        print("⚠️ roster file missing player_id — attempting fallback ID mapping")

        if "gsis_id" in df.columns:
            df = df.rename(columns={"gsis_id": "player_id"})
        elif "nfl_id" in df.columns:
            df = df.rename(columns={"nfl_id": "player_id"})
        else:
            print("❌ No usable ID column found in roster — returning empty roster")
            return pd.DataFrame({"player_id": [], "player_name": [], "team": [], "position": []})

    # Use recent_team as team
    if "recent_team" in df.columns:
        df = df.rename(columns={"recent_team": "team"})

    # Filter to active roster rows only
    if "status" in df.columns:
        df = df[df["status"].isin(["ACT", "PRA", "RES"])]

    # Deduplicate by player_id
    df = df.sort_values("season", ascending=False).drop_duplicates("player_id")

    # Ensure position exists
    if "position" not in df.columns:
        df["position"] = None

    return df

# ============================================================
# UNIFIED WEEKLY LOADER (FIXED FOR POSITION)
# ============================================================

def load_weekly_data(season: int, week: int) -> pd.DataFrame:
    from services.loaders.id_harmonizer import harmonize_ids  # avoid circular import

    print(f"🔥 Loading weekly data from local PBP for {season} week {week}")

    # Load weekly PBP-derived stats
    df = load_weekly_from_pbp(season, week)
    if df.empty:
        print(f"⚠️ No weekly data for {season} week {week}")
        return df

    # ------------------------------------------------------------
    # FIX: Always load real rosters (2025+ included)
    # ------------------------------------------------------------
    try:
        rosters = load_rosters(season)
        print(f"📘 Loaded roster rows: {len(rosters)} for season {season}")
    except Exception as e:
        print(f"⚠️ Failed to load rosters for {season}: {e}")
        rosters = pd.DataFrame({"player_id": [], "player_name": [], "team": [], "position": []})

    # Harmonize IDs + attach player_name, team, position
    df = harmonize_ids(df, rosters)

    # Debug: verify position is present after harmonization
    try:
        print("DEBUG AFTER HARMONIZE (first 10 rows):")
        print(df[["player_id", "player_name", "team", "position"]].head(10))
    except Exception:
        print("⚠️ DEBUG: position column missing after harmonize_ids")

    # ------------------------------------------------------------
    # Snap counts (skip for seasons without data)
    # ------------------------------------------------------------
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

    # Fallback: nflverse 2025+ sometimes uses gsis_id or nfl_id instead of player_id
    if "player_id" not in df.columns:
        print("⚠️ roster file missing player_id — attempting fallback ID mapping")

        if "gsis_id" in df.columns:
            df = df.rename(columns={"gsis_id": "player_id"})
        elif "nfl_id" in df.columns:
            df = df.rename(columns={"nfl_id": "player_id"})
        else:
            print("❌ No usable ID column found in roster — returning empty roster")
            return pd.DataFrame({"player_id": [], "player_name": [], "team": [], "position": []})

    # Use recent_team as team
    if "recent_team" in df.columns:
        df = df.rename(columns={"recent_team": "team"})

    # Filter to active roster rows only
    if "status" in df.columns:
        df = df[df["status"].isin(["ACT", "PRA", "RES"])]

    # Deduplicate by player_id
    df = df.sort_values("season", ascending=False).drop_duplicates("player_id")

    # Ensure position exists
    if "position" not in df.columns:
        df["position"] = None

    return df

# ============================================================
# UNIFIED WEEKLY LOADER (FIXED FOR POSITION)
# ============================================================

def load_weekly_data(season: int, week: int) -> pd.DataFrame:
    from services.loaders.id_harmonizer import harmonize_ids  # avoid circular import

    print(f"🔥 Loading weekly data from local PBP for {season} week {week}")

    # Load weekly PBP-derived stats
    df = load_weekly_from_pbp(season, week)
    if df.empty:
        print(f"⚠️ No weekly data for {season} week {week}")
        return df

    # ------------------------------------------------------------
    # FIX: Always load real rosters (2025+ included)
    # ------------------------------------------------------------
    try:
        rosters = load_rosters(season)
        print(f"📘 Loaded roster rows: {len(rosters)} for season {season}")
    except Exception as e:
        print(f"⚠️ Failed to load rosters for {season}: {e}")
        rosters = pd.DataFrame({"player_id": [], "player_name": [], "team": [], "position": []})

    # Harmonize IDs + attach player_name, team, position
    df = harmonize_ids(df, rosters)

    # Debug: verify position is present after harmonization
    try:
        print("DEBUG AFTER HARMONIZE (first 10 rows):")
        print(df[["player_id", "player_name", "team", "position"]].head(10))
    except Exception:
        print("⚠️ DEBUG: position column missing after harmonize_ids")

    # ------------------------------------------------------------
    # Snap counts (skip for seasons without data)
    # ------------------------------------------------------------
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
# MULTI-WEEK USAGE + FANTASY SCORING + ATTRIBUTION
# ============================================================

@router.get("/nfl/multi-usage-v2/{season}")
def get_multi_week_usage(
    season: int,
    weeks: str,
    position: str = "ALL",
    scoring: str = "standard"
):
    from services.metrics.fantasy_attribution import compute_attribution

    try:
        week_list = [int(w) for w in weeks.split(",") if w.strip()]
    except:
        raise HTTPException(status_code=400, detail="Invalid weeks parameter")

    if not week_list:
        raise HTTPException(status_code=400, detail="No weeks provided")

    pos = position.upper()
    all_rows = []

    for w in week_list:
        df = load_weekly_data(season, w)
        if df.empty or "week" not in df.columns:
            continue

        week_df = df[df["week"] == w]
        if week_df.empty:
            continue

        # Position filter
        if pos == "WR/TE":
            week_df = week_df[week_df["position"].isin(["WR", "TE"])]
        elif pos != "ALL":
            week_df = week_df[week_df["position"] == pos]

        if week_df.empty:
            continue

        # Weekly pipeline
        week_df = present_usage(week_df, pos)
        week_df = apply_scoring(week_df, scoring)
        week_df = compute_attribution(week_df)
        week_df = add_efficiency_metrics(week_df)

        week_df = week_df.replace([np.inf, -np.inf], 0).fillna(0)
        week_df["week"] = w

        all_rows.extend(week_df.to_dict(orient="records"))

    if not all_rows:
        return []

    # ------------------------------------------------------------
    # Aggregate across weeks
    # ------------------------------------------------------------
    aggregated = {}
    for row in all_rows:
        pid = row.get("player_id") or f"{row.get('player_name')}-{row.get('team')}"

        if pid not in aggregated:
            aggregated[pid] = {
                "player_id": pid,
                "player_name": row.get("player_name"),
                "team": row.get("team"),
                "position": row.get("position"),
                "weeks": [],
                "attempts": 0,
                "receptions": 0,
                "touches": 0,
                "total_yards": 0,
                "touchdowns": 0,
                "fantasy_points": 0,
                "fantasy_points_ppr": 0,
                "fantasy_points_half": 0,
                "fantasy_points_shen2000": 0,
                "attr": {
                    "passing_pct": 0,
                    "rushing_pct": 0,
                    "receiving_pct": 0,
                    "td_pct": 0,
                    "bonus_pct": 0,
                    "turnover_pct": 0,
                }
            }

        agg = aggregated[pid]

        # Weeks
        wk = row.get("week")
        if wk not in agg["weeks"]:
            agg["weeks"].append(wk)

        # Usage
        agg["attempts"] += row.get("attempts", 0)
        agg["receptions"] += row.get("receptions", 0)
        agg["touches"] += row.get("touches", 0)
        agg["total_yards"] += row.get("total_yards", 0)
        agg["touchdowns"] += row.get("touchdowns", 0)

        # Fantasy scoring
        agg["fantasy_points"] += row.get("fantasy_points", 0)
        agg["fantasy_points_ppr"] += row.get("fantasy_points_ppr", 0)
        agg["fantasy_points_half"] += row.get("fantasy_points_half", 0)
        agg["fantasy_points_shen2000"] += row.get("fantasy_points_shen2000", 0)

        # Attribution (sum raw, normalize later)
        for key, val in row.get("attr", {}).items():
            agg["attr"][key] += val

    # Normalize attribution to percentages
    for player in aggregated.values():
        total = sum(abs(v) for v in player["attr"].values()) or 1
        for k in player["attr"]:
            player["attr"][k] = round(player["attr"][k] / total * 100, 2)

    result = list(aggregated.values())
    result.sort(key=lambda r: r.get("fantasy_points", 0), reverse=True)

    return result


# ============================================================
# SEASONS ROUTE
# ============================================================

@router.get("/nfl/seasons")
def get_available_seasons():
    if not SEASON_CACHE["loaded"]:
        build_season_cache()
    return SEASON_CACHE["seasons"]

