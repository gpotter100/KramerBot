import polars as pl

# ============================================================
# CANONICAL PBP SCHEMA (your internal contract)
# ============================================================

PBP_SCHEMA = {
    "game_id": pl.Utf8,
    "play_id": pl.Int64,
    "season": pl.Int64,
    "week": pl.Int64,
    "quarter": pl.Int64,
    "time_remaining": pl.Int64,  # seconds remaining in quarter
    "offense_team": pl.Utf8,
    "defense_team": pl.Utf8,
    "yardline_100": pl.Float64,
    "down": pl.Int64,
    "ydstogo": pl.Int64,
    "play_type": pl.Utf8,

    # Passing
    "pass_air_yards": pl.Float64,
    "pass_yac": pl.Float64,

    # Rushing
    "rush_gap": pl.Utf8,
    "rush_direction": pl.Utf8,

    # Advanced metrics
    "epa": pl.Float64,
    "wpa": pl.Float64,
    "success": pl.Int64,

    # Player identifiers
    "qb_id": pl.Utf8,
    "receiver_id": pl.Utf8,
    "rusher_id": pl.Utf8,
}

# ============================================================
# EMPTY DATAFRAME FACTORY
# ============================================================

def empty_pbp_frame() -> pl.LazyFrame:
    """
    Returns an empty LazyFrame with the canonical PBP schema.
    Used when a season has no available PBP data.
    """
    return pl.LazyFrame(schema=PBP_SCHEMA)

# ============================================================
# SCHEMA ENFORCEMENT
# ============================================================

def enforce_schema(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Ensures a LazyFrame conforms to the canonical PBP schema.
    Missing columns are added as nulls.
    Extra columns are ignored.
    Types are cast to the canonical types.
    """
    # Add missing columns
    for col, dtype in PBP_SCHEMA.items():
        if col not in lf.columns:
            lf = lf.with_columns(pl.lit(None, dtype=dtype).alias(col))

    # Cast existing columns to correct types
    lf = lf.with_columns([
        pl.col(col).cast(dtype, strict=False)
        for col, dtype in PBP_SCHEMA.items()
        if col in lf.columns
    ])

    # Select only canonical columns in canonical order
    lf = lf.select(list(PBP_SCHEMA.keys()))

    return lf
