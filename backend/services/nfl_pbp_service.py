from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import polars as pl

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
PBP_CACHE_DIR = BASE_DIR / "tmp" / "kramerbot_pbp_cache"
PBP_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _pbp_path(season: int) -> Path:
    return PBP_CACHE_DIR / f"pbp_{season}.parquet"

NFLVERSE_PBP_URL = (
    "https://github.com/nflverse/nflverse-data/releases/download/pbp/pbp_{season}.parquet"
)


# ---------------------------------------------------------------------------
# Season Loader (cache-first, network fallback)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=6)
def load_pbp_season(season: int) -> pl.DataFrame:
    """
    Loads a full season of PBP data.

    Priority:
    1. Local Parquet cache (your R-generated 2025 file lives here)
    2. nflverse GitHub parquet (for older seasons)
    """
    path = _pbp_path(season)

    # 1. Local cache (preferred)
    if path.exists() and path.stat().st_size > 0:
        return pl.read_parquet(path)

    # 2. Remote fallback (only for seasons where nflverse publishes)
    url = NFLVERSE_PBP_URL.format(season=season)
    df = pl.read_parquet(url)

    # Save for future use
    df.write_parquet(path)
    return df


# ---------------------------------------------------------------------------
# Week Filter
# ---------------------------------------------------------------------------

def pbp_week(season: int, week: int, season_type: str = "REG") -> pl.DataFrame:
    """
    Returns all plays for a given season/week/season_type.
    """
    df = load_pbp_season(season)

    # Defensive filtering — handles missing columns gracefully
    filters = [
        pl.col("season") == season if "season" in df.columns else True,
        pl.col("week") == week if "week" in df.columns else True,
        pl.col("season_type") == season_type if "season_type" in df.columns else True,
    ]

    return df.filter(filters)


# ---------------------------------------------------------------------------
# Games Index (for dropdowns)
# ---------------------------------------------------------------------------

def pbp_games_index(season: int, week: int, season_type: str = "REG") -> list[dict]:
    """
    Returns a small, stable index of games for UI dropdowns.
    Never throws — always returns a list.
    """
    df = pbp_week(season, week, season_type)

    if df.is_empty():
        return []

    # Columns we want to show if available
    cols = [c for c in ["game_id", "game_date", "home_team", "away_team"] if c in df.columns]
    if not cols:
        return []

    games = df.select(cols).unique()

    # Sort defensively
    sort_cols = [c for c in ["game_date", "away_team", "home_team", "game_id"] if c in games.columns]
    if sort_cols:
        games = games.sort(sort_cols, descending=False, nulls_last=True)

    return games.to_dicts()


# ---------------------------------------------------------------------------
# Single Game PBP
# ---------------------------------------------------------------------------

def pbp_by_game(
    season: int,
    week: int,
    game_id: str,
    season_type: str = "REG",
    limit: int | None = None,
) -> list[dict]:
    """
    Returns play-by-play for a single game.
    Payload is trimmed for browser safety.
    """
    df = pbp_week(season, week, season_type)

    if "game_id" not in df.columns:
        return []

    df = df.filter(pl.col("game_id") == game_id)

    if df.is_empty():
        return []

    # Columns safe for UI
    keep = [
        "game_id",
        "qtr",
        "quarter_seconds_remaining",
        "down",
        "ydstogo",
        "yardline_100",
        "posteam",
        "defteam",
        "play_type",
        "desc",
        "epa",
        "wp",
        "wpa",
        "pass",
        "rush",
        "complete_pass",
        "touchdown",
        "interception",
        "fumble_lost",
        "penalty",
        "yards_gained",
    ]
    keep = [c for c in keep if c in df.columns]

    if keep:
        df = df.select(keep)

    # Preserve play ordering
    for order_col in ["play_id", "index", "game_seconds_remaining"]:
        if order_col in df.columns:
            df = df.sort(order_col)
            break

    # Optional limit for browser safety
    if limit is not None:
        df = df.head(limit)

    return df.to_dicts()
