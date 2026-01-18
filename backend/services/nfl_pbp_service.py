from __future__ import annotations

from functools import lru_cache
import polars as pl
from pathlib import Path

PBP_CACHE_DIR = Path("/tmp/kramerbot_pbp_cache")
PBP_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def _pbp_path(season: int) -> Path:
    return PBP_CACHE_DIR / f"pbp_{season}.parquet"


NflversePbpUrl = "https://github.com/nflverse/nflverse-data/releases/download/pbp/pbp_{season}.parquet"


@lru_cache(maxsize=6)
def load_pbp_season(season: int) -> pl.DataFrame:
    path = _pbp_path(season)
    if not path.exists() or path.stat().st_size == 0:
        url = NflversePbpUrl.format(season=season)
        df = pl.read_parquet(url)
        df.write_parquet(path)
        return df
    return pl.read_parquet(path)



def pbp_week(season: int, week: int, season_type: str = "REG") -> pl.DataFrame:
    pbp = load_pbp_season(season)

    # nflfastR uses season_type values like "REG" and "POST"
    out = pbp.filter(
        (pl.col("season") == season)
        & (pl.col("week") == week)
        & (pl.col("season_type") == season_type)
    )
    return out


def pbp_games_index(season: int, week: int, season_type: str = "REG") -> list[dict]:
    df = pbp_week(season, week, season_type)

    # Small, fast “index” for a dropdown
    sort_cols = [c for c in ["game_date", "away_team", "home_team", "game_id"] if c in games.columns]
    if sort_cols:
        games = games.sort(sort_cols, descending=False, nulls_last=True)

        cols = ["game_id"] if "game_id" in df.columns else []

    if not cols:
        return []

    games = (
        df.select(cols)
        .unique()
        .sort(["game_date", "away_team", "home_team"], descending=False, nulls_last=True)
    )
    return games.to_dicts()


def pbp_by_game(season: int, week: int, game_id: str, season_type: str = "REG") -> list[dict]:
    df = pbp_week(season, week, season_type)
    if "game_id" not in df.columns:
        return []

    df = df.filter(pl.col("game_id") == game_id)

    # Keep payload reasonable for the browser; add more fields later as needed.
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

    # Preserve play ordering if available
    for order_col in ["play_id", "index", "game_seconds_remaining"]:
        if order_col in df.columns:
            df = df.sort(order_col)
            break

    return df.to_dicts()
