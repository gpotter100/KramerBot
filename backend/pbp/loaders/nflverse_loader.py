import polars as pl
from pathlib import Path
from pbp.normalize.schema import PBP_SCHEMA

BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_PBP_DIR = BASE_DIR / "tmp" / "kramerbot_pbp_cache"

def load_nflverse_pbp(season: int) -> pl.LazyFrame:
    """
    For 2025:
        Always load from local cached parquet.
    For older seasons:
        Try nflverse parquet URL, fallback to empty schema.
    """
    local_path = LOCAL_PBP_DIR / f"pbp_{season}.parquet"

    # 2025 → always local
    if season == 2025:
        if local_path.exists():
            print(f"🔥 Using local 2025 PBP parquet: {local_path}")
            return pl.scan_parquet(local_path)
        print(f"⚠️ Local 2025 PBP parquet missing: {local_path}")
        return pl.LazyFrame(schema=PBP_SCHEMA)

    # Older seasons → try nflverse
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"pbp/pbp_{season}.parquet"
    )

    try:
        return pl.scan_parquet(url)
    except Exception as e:
        print(f"⚠️ nflverse PBP not available for {season}: {e}")
        return pl.LazyFrame(schema=PBP_SCHEMA)
