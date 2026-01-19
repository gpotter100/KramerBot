import pandas as pd
import numpy as np

from weekly.normalizer import normalize_weekly_df
from services.fantasy.scoring_engine import apply_scoring, coerce_numeric


# ============================================================
#  NUMERIC FIELDS REQUIRED FOR SCORING
# ============================================================

WEEKLY_NUMERIC_FIELDS = [
    "attempts", "carries", "targets", "receptions",
    "passing_yards", "passing_tds", "interceptions",
    "rushing_yards", "rushing_tds",
    "receiving_yards", "receiving_tds",
    "two_point_conversions", "fumbles_lost",
    "fumble_recovery_tds",
    "kick_return_tds", "punt_return_tds",
    "off_fumble_recovery_tds",
    "passing_air_yards", "passing_yac",
    "receiving_air_yards", "receiving_yac",
    "def_sacks", "def_interceptions", "def_fumbles_recovered",
    "def_safeties", "def_tds", "def_return_tds",
    "def_two_point_return", "points_allowed",
    "fg_0_39_made", "fg_40_49_made", "fg_50_plus_made",
    "xp_made", "fg_0_39_missed", "fg_40_49_missed",
    "snap_pct",
]


# ============================================================
#  MAIN WEEKLY LOADER
# ============================================================

def load_weekly_stats(season: int, week: int) -> pd.DataFrame:
    """
    Loads weekly stats from your data source (ESPN, nfl_data_py, parquet, etc.)
    and returns a fully normalized, numeric, schema-stable DataFrame.
    """

    # ------------------------------------------------------------
    # 1. LOAD RAW WEEKLY DATA
    # ------------------------------------------------------------
    try:
        # Replace this with your actual ingestion call:
        # raw = load_from_espn(season, week)
        # raw = load_from_parquet(...)
        # raw = load_from_nfl_data_py(...)
        raw = load_raw_weekly(season, week)   # <--- your existing function
    except Exception as e:
        print(f"[weekly_loader] Failed to load raw weekly data: {e}")
        return pd.DataFrame()

    if raw is None or raw.empty:
        return pd.DataFrame()

    df = raw.copy()

    # ------------------------------------------------------------
    # 2. NORMALIZE COLUMN NAMES + ENSURE SCHEMA
    # ------------------------------------------------------------
    df = normalize_weekly_df(df)

    # ------------------------------------------------------------
    # 3. COERCE ALL NUMERIC FIELDS (critical)
    # ------------------------------------------------------------
    df = coerce_numeric(df, WEEKLY_NUMERIC_FIELDS)

    # ------------------------------------------------------------
    # 4. ENSURE SNAP_PCT EXISTS
    # ------------------------------------------------------------
    if "snap_pct" not in df.columns:
        df["snap_pct"] = 0.0

    # ------------------------------------------------------------
    # 5. ENSURE PLAYER IDENTIFIERS ARE CLEAN
    # ------------------------------------------------------------
    df["player_name"] = df["player_name"].fillna("").astype(str)
    df["team"] = df["team"].fillna("").astype(str)
    df["position"] = df["position"].fillna("").astype(str)

    return df


# ============================================================
#  LOADER + SCORING ENTRY POINT
# ============================================================

def load_weekly_with_scoring(season: int, week: int, scoring: str) -> pd.DataFrame:
    """
    Loads weekly stats, normalizes them, coerces numeric fields,
    applies scoring, and returns a clean DataFrame ready for the API.
    """

    df = load_weekly_stats(season, week)

    if df.empty:
        return df

    # ------------------------------------------------------------
    # 6. APPLY SCORING (standard, ppr, half, vandalay, shen2000)
    # ------------------------------------------------------------
    try:
        df = apply_scoring(df, scoring)
    except Exception as e:
        print(f"[weekly_loader] Scoring failed: {e}")
        # Return unscored data instead of crashing
        return df

    # ------------------------------------------------------------
    # 7. FINAL CLEANUP
    # ------------------------------------------------------------
    df = df.replace({np.nan: 0})

    return df


# ============================================================
#  YOUR EXISTING RAW LOADER (placeholder)
# ============================================================

def load_raw_weekly(season: int, week: int) -> pd.DataFrame:
    """
    This is your existing ingestion function.
    Replace this with your actual ESPN/nfl_data_py/parquet loader.
    """
    raise NotImplementedError("Implement your raw weekly ingestion here.")

import pandas as pd

def load_weekly_pbp(season: int, week: int) -> pd.DataFrame:
    """
    Load play-by-play data for a given season and week.
    Source: nflverse GitHub or your internal storage.
    """
    try:
        url = f"https://github.com/nflverse/nflverse-data/releases/download/pbp/pbp_{season}_week_{week}.parquet"
        df = pd.read_parquet(url)
        df["season"] = season
        df["week"] = week
        return df
    except Exception as e:
        print(f"❌ Failed to load PBP for season {season}, week {week}: {e}")
        return pd.DataFrame()
