import pandas as pd
import numpy as np
from weekly.schema import WEEKLY_SCHEMA


# ============================================================
#  NUMERIC COERCION (critical for scoring)
# ============================================================

NUMERIC_FIELDS = [
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


def coerce_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures all numeric fields are numeric.
    Prevents string arithmetic from breaking scoring.
    """
    for col in NUMERIC_FIELDS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


# ============================================================
#  NORMALIZE NFL WEEKLY DATA
# ============================================================

def normalize_weekly_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes a weekly stats DataFrame into the canonical WEEKLY_SCHEMA.
    Ensures:
      - consistent column names
      - numeric fields coerced to numeric
      - missing columns created but never overwriting existing values
      - no fantasy scoring done here (scoring_engine handles that)
    """

    if df is None or df.empty:
        return empty_weekly_df()

    df = df.copy()

    # ------------------------------------------------------------
    # 1. RENAME COLUMNS TO CANONICAL NAMES
    # ------------------------------------------------------------
    rename_map = {
        "recent_team": "team",
        "club": "team",
        "team_abbr": "team",

        "pass_attempt": "attempts",
        "rush_attempt": "carries",

        "pass_touchdown": "passing_tds",
        "rush_touchdown": "rushing_tds",
        "rec_touchdown": "receiving_tds",

        "pass_yards": "passing_yards",
        "rush_yards": "rushing_yards",
        "rec_yards": "receiving_yards",

        "pass_air_yards": "passing_air_yards",
        "pass_yac": "passing_yac",
        "rec_air_yards": "receiving_air_yards",
        "rec_yac": "receiving_yac",
    }

    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # ------------------------------------------------------------
    # 2. ENSURE RECEPTIONS EXISTS
    # ------------------------------------------------------------
    if "receptions" not in df.columns:
        df["receptions"] = 0

    # ------------------------------------------------------------
    # 3. COERCE NUMERIC FIELDS
    # ------------------------------------------------------------
    df = coerce_numeric(df)

    # ------------------------------------------------------------
    # 4. ENSURE ALL REQUIRED COLUMNS EXIST (NO OVERWRITES)
    # ------------------------------------------------------------
    for col in WEEKLY_SCHEMA:
        if col not in df.columns:
            if col in ["player_name", "player_id", "team", "position"]:
                df[col] = ""
            else:
                df[col] = 0

    # ------------------------------------------------------------
    # 5. SNAP PERCENTAGE FALLBACK
    # ------------------------------------------------------------
    if "snap_pct" not in df.columns:
        df["snap_pct"] = 0.0

    # ------------------------------------------------------------
    # 6. FINAL COLUMN ORDER
    # ------------------------------------------------------------
    df = df[WEEKLY_SCHEMA]

    return df


# ============================================================
#  EMPTY WEEKLY DATAFRAME
# ============================================================

def empty_weekly_df() -> pd.DataFrame:
    return pd.DataFrame({col: [] for col in WEEKLY_SCHEMA})
