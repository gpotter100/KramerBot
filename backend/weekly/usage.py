import pandas as pd


def aggregate_player_usage(week_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates normalized weekly data into player-level usage.
    """

    if week_df.empty:
        return week_df

    usage = (
        week_df
        .groupby("player_name", as_index=False)
        .agg({
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
        })
    )

    return usage
