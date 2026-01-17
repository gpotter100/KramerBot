import polars as pl
from pbp.normalize.schema import PBP_SCHEMA

def load_nflverse_pbp(season: int) -> pl.LazyFrame:
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"pbp/pbp_{season}.parquet"
    )

    try:
        lf = pl.scan_parquet(url)
        return lf
    except Exception as e:
        print(f"⚠️ nflverse PBP not available for {season}: {e}")
        return pl.LazyFrame(schema=PBP_SCHEMA)
