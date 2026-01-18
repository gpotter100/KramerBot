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
    - Normalize columns
    - Filter to active players
    - Deduplicate by player_id
    - Keep only relevant identity fields
    """
    r = rosters.copy()

    # Normalize column names
    r.columns = [c.lower() for c in r.columns]

    # Normalize team column
    if "team" not in r.columns and "recent_team" in r.columns:
        r = r.rename(columns={"recent_team": "team"})

    # Normalize player name column
    if "player_name" not in r.columns and "full_name" in r.columns:
        r = r.rename(columns={"full_name": "player_name"})

    # Filter to active roster rows if status exists
    if "status" in r.columns:
        r = r[r["status"].isin(["ACT", "PRA", "RES"])]

    # Drop rows with no player_id
    if "player_id" in r.columns:
        r = r[r["player_id"].notna()]

    # Deduplicate by player_id (keep most recent if season exists)
    if "season" in r.columns:
        r = r.sort_values("season", ascending=False).drop_duplicates("player_id")
    else:
        r = r.drop_duplicates("player_id")

    # Keep only identity fields
    keep_cols = [c for c in ["player_id", "player_name", "team", "position"] if c in r.columns]
    r = r[keep_cols].copy()

    return r


def harmonize_ids(weekly: pd.DataFrame, rosters: pd.DataFrame) -> pd.DataFrame:
    """
    Harmonizes player_id, player_name, team, and position using roster data.

    Rules:
    - Never overwrite good PBP values
    - Only fill missing values from roster
    - Backfill player_id using name+team when safe
    """

    if weekly.empty or rosters.empty:
        return weekly

    w = weekly.copy()
    w = _ensure_columns(w, ["player_id", "player_name", "team", "position"])

    r = _prepare_roster(rosters)

    # If roster doesn't have player_id, bail out
    if "player_id" not in r.columns:
        return w

    # ------------------------------------------------------------
    # 1. Join on player_id (strongest key)
    # ------------------------------------------------------------
    merged = w.merge(
        r,
        on="player_id",
        how="left",
        suffixes=("", "_roster"),
    )

    # ------------------------------------------------------------
    # 2. Backfill missing player_id using player_name + team
    # ------------------------------------------------------------
    missing_id_mask = merged["player_id"].isna()

    if missing_id_mask.any():
        w_missing = merged[missing_id_mask].copy()

        if "player_name" in r.columns and "team" in r.columns:
            r_name_team = r[["player_id", "player_name", "team", "position"]].drop_duplicates()

            w_missing = w_missing.merge(
                r_name_team,
                on=["player_name", "team"],
                how="left",
                suffixes=("", "_by_name"),
            )

            # Backfill player_id
            merged.loc[missing_id_mask, "player_id"] = w_missing["player_id_by_name"].values

            # Backfill position_roster
            merged["position_roster"] = merged.get("position_roster", None)
            merged.loc[missing_id_mask, "position_roster"] = w_missing["position"].values

    # ------------------------------------------------------------
    # 3. Finalize identity fields (never overwrite good values)
    # ------------------------------------------------------------

    # Position
    if "position_roster" in merged.columns:
        merged["position"] = merged["position"].fillna(merged["position_roster"])

    # Team
    if "team_roster" in merged.columns:
        merged["team"] = merged["team"].fillna(merged["team_roster"])

    # Player name
    if "player_name_roster" in merged.columns:
        merged["player_name"] = merged["player_name"].fillna(merged["player_name_roster"])

    # ------------------------------------------------------------
    # 4. Clean up temporary columns
    # ------------------------------------------------------------
    drop_cols = [c for c in merged.columns if c.endswith("_roster") or c.endswith("_by_name")]
    merged = merged.drop(columns=drop_cols, errors="ignore")

    return merged
