import polars as pl
from pbp.loaders.nflverse_loader import load_nflverse_pbp
from pbp.loaders.espn_loader import load_espn_pbp
from pbp.normalize.schema import PBP_SCHEMA

def load_pbp_for_season(season: int) -> pl.LazyFrame:
    if season <= 2024:
        return load_nflverse_pbp(season)

    # 2025+ (placeholder)
    return load_espn_pbp(season)
