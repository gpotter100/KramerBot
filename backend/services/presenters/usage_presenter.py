import pandas as pd

def present_usage(df: pd.DataFrame, position: str = "ALL") -> pd.DataFrame:
    """
    Premium presentation layer for weekly usage + scoring + metrics.
    Dynamically selects the best column set based on position and
    gracefully handles missing columns.
    """

    df = df.copy()

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
