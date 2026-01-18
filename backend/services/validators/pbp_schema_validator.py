import polars as pl

CANONICAL_PBP_SCHEMA = {
    "season": pl.Int64,
    "week": pl.Int64,
    "game_id": pl.Utf8,
    "play_id": pl.Int64,

    "posteam": pl.Utf8,
    "defteam": pl.Utf8,

    "quarter": pl.Int64,
    "time": pl.Utf8,
    "time_remaining": pl.Float64,
    "down": pl.Int64,
    "ydstogo": pl.Int64,
    "yardline_100": pl.Int64,

    "pass_attempt": pl.Int64,
    "rush_attempt": pl.Int64,
    "sack": pl.Int64,
    "qb_scramble": pl.Int64,
    "touchdown": pl.Int64,
    "interception": pl.Int64,
    "fumble": pl.Int64,
    "complete_pass": pl.Int64,
    "first_down": pl.Int64,

    "passer_id": pl.Utf8,
    "passer": pl.Utf8,
    "rusher_id": pl.Utf8,
    "rusher": pl.Utf8,
    "receiver_id": pl.Utf8,
    "receiver": pl.Utf8,

    "yards_gained": pl.Int64,
    "air_yards": pl.Float64,
    "yards_after_catch": pl.Float64,

    "epa": pl.Float64,
    "wpa": pl.Float64,
    "success": pl.Int64,

    "play_type": pl.Utf8,
    "desc": pl.Utf8,
}


def validate_pbp_schema(df: pl.DataFrame) -> list[str]:
    """
    Returns a list of missing or mismatched columns.
    """
    issues = []

    for col, dtype in CANONICAL_PBP_SCHEMA.items():
        if col not in df.columns:
            issues.append(f"Missing column: {col}")
        else:
            if df[col].dtype != dtype:
                issues.append(f"Column {col} has wrong dtype: {df[col].dtype} != {dtype}")

    return issues
