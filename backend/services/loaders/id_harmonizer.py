import pandas as pd


def _ensure_columns(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """
    Ensure the given columns exist in the DataFrame.
    Missing columns are created with None.
    """
    d = df.copy()
    for col in cols:
        if col not in d.columns:
            d[col] = None
    return d


def _prepare_roster(rosters: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare roster DataFrame for joining:
    - Keep only relevant columns
    - Drop duplicates
    - Normalize column names where possible
    """
    r = rosters.copy()

    # Normalize team column
    if "team" not in r.columns and "recent_team" in r.columns:
        r = r.rename(columns={"recent_team": "team"})

    # Normalize player name column
    if "player_name" not in r.columns and "full_name" in r.columns:
        r = r.rename(columns={"full_name": "player_name"})

    keep_cols = [c for c in ["player_id", "player_name", "team", "position"] if c in r.columns]
    r = r[keep_cols].drop_duplicates()

    return r


def harmonize_ids(weekly: pd.DataFrame, rosters: pd.DataFrame) -> pd.DataFrame:
    """
    Harmonizes player_id, player_name, team, and position using roster data.

    Strategy:
    1. Ensure weekly has player_id, player_name, team, position columns.
    2. Prepare roster with normalized columns.
    3. First join on player_id (strongest key).
    4. For rows still missing player_id, backfill using player_name + team.
    5. Fill position from roster where missing.

    Returns a new DataFrame with harmonized identity fields.
    """

    if weekly.empty or rosters.empty:
        return weekly

    w = weekly.copy()
    w = _ensure_columns(w, ["player_id", "player_name", "team", "position"])

    r = _prepare_roster(rosters)

    # If roster doesn't have player_id, we can't do much
    if "player_id" not in r.columns:
        return w

    # ------------------------------------------------------------
    # 1. Join on player_id (strongest key)
    # ------------------------------------------------------------
    merged = w.merge(
        r,
        on=["player_id"],
        how="left",
        suffixes=("", "_roster"),
    )

    # ------------------------------------------------------------
    # 2. Backfill player_id using player_name + team
    # ------------------------------------------------------------
    missing_id_mask = merged["player_id"].isna()

    if missing_id_mask.any():
        # Subset of weekly rows missing player_id
        w_missing = merged[missing_id_mask].copy()

        # Build a roster index by name + team
        if "player_name" in r.columns and "team" in r.columns:
            r_name_team = r[["player_id", "player_name", "team", "position"]].drop_duplicates()
            w_missing = w_missing.merge(
                r_name_team,
                left_on=["player_name", "team"],
                right_on=["player_name", "team"],
                how="left",
                suffixes=("", "_by_name"),
            )

            # Backfill player_id and position where found
            merged.loc[missing_id_mask, "player_id"] = w_missing["player_id_by_name"].values
            if "position_roster" in merged.columns:
                merged.loc[missing_id_mask, "position_roster"] = w_missing["position"].values
            else:
                merged["position_roster"] = merged.get("position_roster", None)
                merged.loc[missing_id_mask, "position_roster"] = w_missing["position"].values

    # ------------------------------------------------------------
    # 3. Finalize position
    # ------------------------------------------------------------
    if "position" not in merged.columns:
        merged["position"] = None

    if "position_roster" in merged.columns:
        merged["position"] = merged["position"].fillna(merged["position_roster"])

    # ------------------------------------------------------------
    # 4. Clean up extra columns
    # ------------------------------------------------------------
    drop_cols = [c for c in merged.columns if c.endswith("_roster") or c.endswith("_by_name")]
    merged = merged.drop(columns=drop_cols, errors="ignore")

    return merged
