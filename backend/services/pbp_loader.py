from pathlib import Path
import polars as pl

# ------------------------------------------------------------
# Resolve the backend root and cache directory
# ------------------------------------------------------------

# This file lives in: backend/services/pbp_loader.py
# So parents[2] = backend/
BASE_DIR = Path(__file__).resolve().parents[2]

LOCAL_PBP_DIR = BASE_DIR / "data" / "pbp"


# ------------------------------------------------------------
# Unified PBP Loader
# ------------------------------------------------------------

def load_pbp_local(season: int) -> pl.LazyFrame:
    """
    Load PBP for a season from the local parquet files generated
    by the R ingestion pipeline.

    This is the single source of truth for all PBP loading.
    """

    path = LOCAL_PBP_DIR / f"pbp_{season}.parquet"

    if not path.exists():
        print(f"⚠️ Local PBP parquet missing for {season}: {path}")
        return pl.LazyFrame()

    print(f"🔥 Loading local PBP parquet for {season}: {path}")
    return pl.scan_parquet(path)
