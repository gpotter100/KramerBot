import pandas as pd

def present_usage(df: pd.DataFrame, position: str = "ALL") -> pd.DataFrame:
    df = df.copy()

    # ============================================================
    # ROUNDING
    # ============================================================
    fantasy_cols = [
        "fantasy_points",
        "fantasy_points_ppr",
        "fantasy_points_0.5ppr",
    ]
    for col in fantasy_cols:
        if col in df.columns:
            df[col] = df[col].round(2)

    if "snap_pct" in df.columns:
        df["snap_pct"] = df["snap_pct"].round(1)

    # ============================================================
    # PREMIUM COLUMN SETS
    # ============================================================

    ALL_COLUMNS = [
        # Identity
        "player_name", "team", "position", "snap_pct",

        # Receiving usage
        "targets", "receptions", "receiving_yards", "receiving_tds",
        "air_yards", "target_share", "receiving_first_downs",

        # Rushing usage
        "carries", "rushing_yards", "rushing_tds",

        # Passing usage
        "attempts", "passing_yards", "passing_tds", "interceptions",

        # Efficiency
        "receiving_epa", "rushing_epa", "passing_epa",

        # Fantasy
        "fantasy_points", "fantasy_points_ppr", "fantasy_points_0.5ppr",
    ]

    WR_TE_COLUMNS = [
        "player_name", "team", "position", "snap_pct",

        # Receiving usage
        "targets", "receptions", "receiving_yards", "receiving_tds",
        "air_yards", "target_share", "receiving_first_downs",

        # Rushing usage (added per your request)
        "carries", "rushing_yards", "rushing_tds",

        # Efficiency
        "receiving_epa", "rushing_epa",

        # Fantasy
        "fantasy_points_ppr",
    ]

    RB_COLUMNS = [
        "player_name", "team", "position", "snap_pct",
        "carries", "rushing_yards", "rushing_tds",
        "targets", "receptions", "receiving_yards",
        "rushing_epa", "receiving_epa",
        "fantasy_points_ppr",
    ]

    QB_COLUMNS = [
        "player_name", "team", "position", "snap_pct",
        "attempts", "passing_yards", "passing_tds", "interceptions",
        "rushing_yards", "rushing_tds",
        "passing_epa",
        "fantasy_points",
    ]

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
