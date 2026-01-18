from pathlib import Path
import polars as pl
from pbp.normalize.schema import PBP_SCHEMA
from pbp.loaders.nflverse_loader import load_nflverse_pbp

BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_PBP_DIR = BASE_DIR / "tmp" / "kramerbot_pbp_cache"

def load_pbp_for_season(season: int) -> pl.LazyFrame:
    """
    Unified PBP loader:
    - 2025 → always load from local parquet
    - <= 2024 → nflverse parquet
    - future → empty schema for now
    """
    local_path = LOCAL_PBP_DIR / f"pbp_{season}.parquet"

    # 2025 → always local
    if season == 2025:
        if local_path.exists():
            print(f"🔥 Using local PBP for {season}: {local_path}")
            return pl.scan_parquet(local_path)
        print(f"⚠️ Missing local PBP for {season}: {local_path}")
        return pl.LazyFrame(schema=PBP_SCHEMA)

    # Historical seasons → nflverse
    if season <= 2024:
        return load_nflverse_pbp(season)

    # Future seasons → placeholder
    print(f"⚠️ No PBP loader for {season} yet")
    return pl.LazyFrame(schema=PBP_SCHEMA)
