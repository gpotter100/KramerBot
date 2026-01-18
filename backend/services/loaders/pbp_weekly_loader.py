import pandas as pd
import polars as pl
from pathlib import Path

# ------------------------------------------------------------
# Local PBP directory (written by your R ingestion pipeline)
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_PBP_DIR = BASE_DIR / "tmp" / "kramerbot_pbp_cache"


# ------------------------------------------------------------
# Unified PBP Loader (local parquet only)
# ------------------------------------------------------------
def load_pbp_local(season: int) -> pl.LazyFrame:
    """
    Loads PBP for a season from local parquet written by the R ingestion pipeline.
    """
    path = LOCAL_PBP_DIR / f"pbp_{season}.parquet"

    if not path.exists():
        print(f"⚠️ Missing local PBP parquet for {season}: {path}")
        return pl.LazyFrame()

    print(f"🔥 Loading local PBP parquet for {season}: {path}")
    return pl.scan_parquet(path)


# ------------------------------------------------------------
# Weekly Builder (PBP → player-level weekly stats)
# ------------------------------------------------------------
def load_weekly_from_pbp(season: int, week: int) -> pd.DataFrame:
    """
    Builds weekly player-level stats from local PBP parquet.
    This is the unified weekly builder for ALL seasons.
    """

    lf = load_pbp_local(season)
    if lf.is_empty():
        return pd.DataFrame()

    # Filter to week
    lf_week = lf.filter(pl.col("week") == week)

    # Collect to pandas for now (Phase 2 will stay in Polars)
    try:
        pbp_week = lf_week.collect().to_pandas()
    except Exception:
        return pd.DataFrame()

    if pbp_week.empty:
        return pd.DataFrame()

    # ------------------------------------------------------------
    # RECEIVING
    # ------------------------------------------------------------
    rec_events = pbp_week[pbp_week.get("pass_attempt", 0) == 1]
    rec_df = (
        rec_events.groupby(["receiver_id", "receiver", "posteam"], dropna=True)
        .agg(
            targets=("receiver_id", "count"),
            receptions=("complete_pass", "sum"),
            receiving_yards=("yards_gained", "sum"),
            receiving_tds=("touchdown", "sum"),
            receiving_air_yards=("air_yards", "sum"),
            receiving_first_downs=("first_down", "sum"),
            receiving_epa=("epa", "sum"),
        )
        .reset_index()
        .rename(
            columns={
                "receiver_id": "player_id",
                "receiver": "player_name",
                "posteam": "team",
            }
        )
    )

    # ------------------------------------------------------------
    # RUSHING
    # ------------------------------------------------------------
    rush_events = pbp_week[pbp_week.get("rush_attempt", 0) == 1]
    rush_df = (
        rush_events.groupby(["rusher_id", "rusher", "posteam"], dropna=True)
        .agg(
            carries=("rusher_id", "count"),
            rushing_yards=("yards_gained", "sum"),
            rushing_tds=("touchdown", "sum"),
            rushing_epa=("epa", "sum"),
        )
        .reset_index()
        .rename(
            columns={
                "rusher_id": "player_id",
                "rusher": "player_name",
                "posteam": "team",
            }
        )
    )

    # ------------------------------------------------------------
    # PASSING
    # ------------------------------------------------------------
    pass_events = pbp_week[pbp_week.get("pass_attempt", 0) == 1]
    pass_df = (
        pass_events.groupby(["passer_id", "passer", "posteam"], dropna=True)
        .agg(
            attempts=("pass_attempt", "sum"),
            completions=("complete_pass", "sum"),
            passing_yards=("yards_gained", "sum"),
            passing_tds=("touchdown", "sum"),
            interceptions=("interception", "sum"),
            passing_air_yards=("air_yards", "sum"),
            passing_first_downs=("first_down", "sum"),
            passing_epa=("epa", "sum"),
        )
        .reset_index()
        .rename(
            columns={
                "passer_id": "player_id",
                "passer": "player_name",
                "posteam": "team",
            }
        )
    )

    # ------------------------------------------------------------
    # MERGE ALL THREE
    # ------------------------------------------------------------
    from functools import reduce

    dfs = [rec_df, rush_df, pass_df]
    dfs = [df for df in dfs if not df.empty]

    if not dfs:
        return pd.DataFrame()

    weekly = reduce(
        lambda left, right: pd.merge(
            left, right, on=["player_id", "player_name", "team"], how="outer"
        ),
        dfs,
    )

    weekly["season"] = season
    weekly["week"] = week

    # ------------------------------------------------------------
    # FANTASY SCORING
    # ------------------------------------------------------------
    for col in [
        "targets", "receptions", "receiving_yards", "receiving_tds",
        "carries", "rushing_yards", "rushing_tds",
        "attempts", "passing_yards", "passing_tds", "interceptions"
    ]:
        if col not in weekly.columns:
            weekly[col] = 0

    weekly["fantasy_points"] = (
        weekly["rushing_yards"] / 10
        + weekly["receiving_yards"] / 10
        + weekly["rushing_tds"] * 6
        + weekly["receiving_tds"] * 6
        + weekly["passing_yards"] / 25
        + weekly["passing_tds"] * 4
        - weekly["interceptions"] * 2
    )

    weekly["fantasy_points_ppr"] = weekly["fantasy_points"] + weekly["receptions"]
    weekly["fantasy_points_0.5ppr"] = weekly["fantasy_points"] + weekly["receptions"] * 0.5

    return weekly
