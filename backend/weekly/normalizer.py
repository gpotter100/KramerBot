import pandas as pd
from weekly.schema import WEEKLY_SCHEMA


# ============================================================
# NORMALIZE NFL WEEKLY DATA (nfl_data_py or ESPN)
# ============================================================

def normalize_weekly_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes a weekly stats DataFrame into the canonical WEEKLY_SCHEMA.
    Ensures:
      - consistent column names
      - all required columns exist
      - missing values filled with 0
      - fantasy_points_0.5ppr calculated
    """

    if df is None or df.empty:
        return empty_weekly_df()

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
    # 2. ENSURE RECEPTIONS EXISTS BEFORE CALCULATING 0.5 PPR
    # ------------------------------------------------------------
    if "receptions" not in df.columns:
        df["receptions"] = 0

    # ------------------------------------------------------------
    # 3. CALCULATE 0.5 PPR FANTASY POINTS
    # ------------------------------------------------------------
    df["fantasy_points_0.5ppr"] = (
        df.get("fantasy_points", 0) + 0.5 * df.get("receptions", 0)
    )

    # ------------------------------------------------------------
    # 4. ENSURE ALL REQUIRED COLUMNS EXIST
    # ------------------------------------------------------------
    for col in WEEKLY_SCHEMA:
        if col not in df.columns:
            # numeric columns default to 0, strings default to ""
            df[col] = 0 if col not in ["player_name", "player_id", "team", "position"] else ""

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
# EMPTY WEEKLY DATAFRAME (for missing seasons)
# ============================================================

def empty_weekly_df() -> pd.DataFrame:
    """
    Returns an empty DataFrame with the canonical WEEKLY_SCHEMA.
    """
    df = pd.DataFrame({col: [] for col in WEEKLY_SCHEMA})
    return df
