import pandas as pd

CANONICAL_WEEKLY_COLUMNS = [
    "season", "week",
    "player_id", "player_name", "team", "position",

    # Passing
    "attempts", "completions", "passing_yards", "passing_tds",
    "interceptions", "passing_air_yards", "passing_first_downs",
    "passing_epa",

    # Rushing
    "carries", "rushing_yards", "rushing_tds",
    "rushing_fumbles", "rushing_fumbles_lost",
    "rushing_first_downs", "rushing_epa",

    # Receiving
    "targets", "receptions", "receiving_yards", "receiving_tds",
    "receiving_air_yards", "receiving_first_downs", "receiving_epa",

    # Fantasy
    "fantasy_points", "fantasy_points_ppr", "fantasy_points_0.5ppr",

    # Meta
    "snap_pct",
]


def validate_weekly_schema(df: pd.DataFrame) -> list[str]:
    missing = [col for col in CANONICAL_WEEKLY_COLUMNS if col not in df.columns]
    return missing
