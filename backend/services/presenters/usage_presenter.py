import pandas as pd
import numpy as np

# ============================================================
#  PRESENT WEEKLY OR MULTI-WEEK USAGE
# ============================================================

def present_usage(df: pd.DataFrame, position_filter: str = "ALL") -> pd.DataFrame:
    """
    Produces a clean, frontend-ready usage dataframe.
    - Preserves player_name, team, position
    - Aggregates numeric usage fields
    - Supports WR/TE combined filtering
    - Supports ALL positions
    """

    if df.empty:
        return df

    # Ensure required identity columns exist
    for col in ["player_id", "player_name", "team", "position"]:
        if col not in df.columns:
            df[col] = ""

    # Normalize position
    df["position"] = df["position"].fillna("").astype(str).str.upper()

    # Apply position filter BEFORE aggregation
    pos = (position_filter or "ALL").upper()

    if pos == "WR/TE":
        df = df[df["position"].isin(["WR", "TE"])]
    elif pos != "ALL":
        df = df[df["position"] == pos]

    if df.empty:
        return df

    # Identify numeric usage fields (safe auto-detection)
    numeric_cols = [
        c for c in df.columns
        if df[c].dtype != "object"
        and c not in ["week", "season"]
    ]

    # Identity columns preserved via "first"
    identity_cols = ["player_id", "player_name", "team", "position"]

    agg_dict = {col: "first" for col in identity_cols}
    agg_dict.update({col: "sum" for col in numeric_cols})

    # Group by player_id (canonical)
    grouped = df.groupby("player_id", as_index=False).agg(agg_dict)

    # Recompute derived usage metrics
    grouped["touches"] = (
        grouped.get("attempts", 0)
        + grouped.get("receptions", 0)
    )

    grouped["total_yards"] = (
        grouped.get("passing_yards", 0)
        + grouped.get("rushing_yards", 0)
        + grouped.get("receiving_yards", 0)
    )

    grouped["total_tds"] = (
        grouped.get("passing_tds", 0)
        + grouped.get("rushing_tds", 0)
        + grouped.get("receiving_tds", 0)
    )

    # Weeks played (for multi-week)
    if "week" in df.columns:
        grouped["weeks"] = df.groupby("player_id")["week"].nunique().values
    else:
        grouped["weeks"] = 1

    # Clean up NaN / inf
    grouped = grouped.replace([np.inf, -np.inf], 0).fillna(0)

    return grouped

    # ============================================================
    # ROUNDING
    # ============================================================
    round_2 = [
        "fantasy_points",
        "fantasy_points_ppr",
        "fantasy_points_0.5ppr",
        "vandalay_points",
        "vandalay_def_points",
        "vandalay_total_points",
        "fantasy_per_touch",
        "vandalay_per_touch",
        "yards_per_target",
        "yards_per_reception",
        "yards_per_carry",
        "yards_per_attempt",
        "td_rate",
        "int_rate",
    ]

    for col in round_2:
        if col in df.columns:
            df[col] = df[col].round(2)

    if "snap_pct" in df.columns:
        df["snap_pct"] = df["snap_pct"].round(1)

    # ============================================================
    # PREMIUM COLUMN SETS
    # ============================================================

    # --- Universal identity columns ---
    IDENTITY = [
        "player_name", "team", "position", "snap_pct"
    ]

    # --- Core usage columns ---
    RECEIVING = [
        "targets", "receptions", "receiving_yards", "receiving_tds",
        "receiving_air_yards", "receiving_first_downs",
    ]

    RUSHING = [
        "carries", "rushing_yards", "rushing_tds",
        "rushing_first_downs",
    ]

    PASSING = [
        "attempts", "completions", "passing_yards",
        "passing_tds", "interceptions",
        "passing_air_yards", "passing_first_downs",
    ]

    # --- Efficiency metrics ---
    EFFICIENCY = [
        "yards_per_target", "yards_per_reception",
        "yards_per_carry", "yards_per_attempt",
        "td_rate", "int_rate",
        "receiving_epa", "rushing_epa", "passing_epa",
    ]

    # --- Fantasy scoring ---
    FANTASY = [
        "fantasy_points",
        "fantasy_points_ppr",
        "fantasy_points_0.5ppr",
        "vandalay_points",
        "vandalay_def_points",
        "vandalay_total_points",
        "fantasy_per_touch",
        "vandalay_per_touch",
    ]

    # --- Attribution percentages (only include if present) ---
    ATTRIBUTION = [c for c in df.columns if c.endswith("_pts_pct")]

    # ============================================================
    # POSITION‑AWARE COLUMN GROUPS
    # ============================================================

    ALL_COLUMNS = (
        IDENTITY +
        RECEIVING +
        RUSHING +
        PASSING +
        EFFICIENCY +
        FANTASY +
        ATTRIBUTION
    )

    WR_TE_COLUMNS = (
        IDENTITY +
        RECEIVING +
        RUSHING +  # WR rushing usage is valuable
        ["yards_per_target", "yards_per_reception"] +
        ["receiving_epa", "rushing_epa"] +
        ["fantasy_points_ppr", "vandalay_points"] +
        ATTRIBUTION
    )

    RB_COLUMNS = (
        IDENTITY +
        RUSHING +
        RECEIVING +  # RB receiving usage matters
        ["yards_per_carry", "yards_per_target"] +
        ["rushing_epa", "receiving_epa"] +
        ["fantasy_points_ppr", "vandalay_points"] +
        ATTRIBUTION
    )

    QB_COLUMNS = (
        IDENTITY +
        PASSING +
        RUSHING +  # QB rushing matters
        ["yards_per_attempt", "td_rate", "int_rate"] +
        ["passing_epa", "rushing_epa"] +
        ["fantasy_points", "vandalay_points"] +
        ATTRIBUTION
    )

    # ============================================================
    # SELECT COLUMN SET BASED ON POSITION
    # ============================================================

    pos = position.upper()

    if pos == "QB":
        col_order = QB_COLUMNS
    elif pos == "RB":
        col_order = RB_COLUMNS
    elif pos in ("WR", "TE", "WR/TE"):
        col_order = WR_TE_COLUMNS
    else:
        col_order = ALL_COLUMNS

    # Only keep columns that exist in the DF
    col_order = [c for c in col_order if c in df.columns]

    return df[col_order]
