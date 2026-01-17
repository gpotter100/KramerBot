import polars as pl
from pbp.normalize.schema import PBP_SCHEMA

def load_espn_pbp(season: int) -> pl.LazyFrame:
    print(f"⚠️ No ESPN PBP implemented yet for {season}. Returning empty.")
    return pl.LazyFrame(schema=PBP_SCHEMA)
