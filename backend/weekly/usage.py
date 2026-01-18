import pandas as pd


def aggregate_player_usage(week_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates normalized weekly data into player-level usage.

    Expects columns like:
    - attempts, completions, passing_yards, receptions, carries, etc.
    - team, position, snap_pct
    - fantasy_points, fantasy_points_ppr, fantasy_points_0.5ppr

    Returns one row per player_id + player_name (if player_id exists),
    otherwise falls back to player_name only.
    """

    if week_df.empty:
        return week_df

    # ------------------------------------------------------------
    # Define aggregation map (schema-aware)
    # ------------------------------------------------------------
    agg_map = {
        # Passing
        "attempts": "sum",
        "completions": "sum",
        "passing_yards": "sum",
        "passing_tds": "sum",
        "interceptions": "sum",
        "passing_air_yards": "sum",
        "passing_first_downs": "sum",
        "passing_epa": "sum",

        # Rushing
        "carries": "sum",
        "rushing_yards": "sum",
        "rushing_tds": "sum",
        "rushing_fumbles": "sum",
        "rushing_fumbles_lost": "sum",
        "rushing_first_downs": "sum",
        "rushing_epa": "sum",

        # Receiving
        "receptions": "sum",
        "targets": "sum",
        "receiving_yards": "sum",
        "receiving_tds": "sum",
        "receiving_air_yards": "sum",
        "receiving_first_downs": "sum",
        "receiving_epa": "sum",

        # Fantasy
        "fantasy_points": "sum",
        "fantasy_points_ppr": "sum",
        "fantasy_points_0.5ppr": "sum",

        # Meta
        "team": "first",
        "position": "first",
        "snap_pct": "mean",
    }

    # ------------------------------------------------------------
    # Filter to only existing columns
    # ------------------------------------------------------------
    existing_cols = set(week_df.columns)
    safe_agg_map = {k: v for k, v in agg_map.items() if k in existing_cols}

    # ------------------------------------------------------------
    # Choose groupby keys
    # ------------------------------------------------------------
    group_keys = ["player_name"]
    if "player_id" in week_df.columns:
        group_keys = ["player_id", "player_name"]

    # ------------------------------------------------------------
    # Aggregate
    # ------------------------------------------------------------
    usage = (
        week_df
        .groupby(group_keys, as_index=False)
        .agg(safe_agg_map)
    )

    return usage
