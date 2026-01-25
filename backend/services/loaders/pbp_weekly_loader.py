import pandas as pd
import polars as pl
from pathlib import Path

# ------------------------------------------------------------
# Local PBP directory (written by your R ingestion pipeline)
# ------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_PBP_DIR = BASE_DIR / "data" / "pbp"   # <-- UPDATED PATH


# ------------------------------------------------------------
# Unified PBP Loader (local parquet only)
# ------------------------------------------------------------
def load_pbp_local(season: int) -> pl.LazyFrame:
    """
    Loads PBP for a season from local parquet written by the R ingestion pipeline.
    Always returns a LazyFrame (may be empty).
    """
    path = LOCAL_PBP_DIR / f"pbp_{season}.parquet"

    if not path.exists():
        print(f"⚠️ Missing local PBP parquet for {season}: {path}")
        return pl.LazyFrame()  # empty LF

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

    # ------------------------------------------------------------
    # FIX #1 — LazyFrame has no .is_empty(), so we check via collect()
    # ------------------------------------------------------------
    try:
        # Filter by week inside Polars (fast)
        lf_week = lf.filter(pl.col("week") == week)

        # Collect to pandas
        pbp_week = lf_week.collect().to_pandas()
    except Exception as e:
        print(f"❌ ERROR collecting PBP for {season} week {week}: {e}")
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
            fumbles_lost=("fumble_lost", lambda x: (
                (rec_events.loc[x.index, "fumble_lost"] == 1) &
                (rec_events.loc[x.index, "receiver_id"].notna())
            ).sum()),

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
            fumbles_lost=("fumble_lost", lambda x: (
                (rush_events.loc[x.index, "fumble_lost"] == 1) &
                (rush_events.loc[x.index, "rusher_id"].notna())
            ).sum()),

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
            
            interceptions=("interception", lambda x: (
                (pass_events.loc[x.index, "pass_attempt"] == 1) &
                (pass_events.loc[x.index, "interception"] == 1) &
                (pass_events.loc[x.index, "passer_id"].notna())
            ).sum()),

            fumbles_lost=("fumble_lost", lambda x: (
                (pass_events.loc[x.index, "fumble_lost"] == 1) &
                (pass_events.loc[x.index, "passer_id"].notna())
            ).sum()),

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

    # ------------------------------------------------------------
    # CLEAN UP ROLE-SPECIFIC STAT COLUMNS
    # ------------------------------------------------------------

    def sum_columns(df, base_name):
        cols = [c for c in df.columns if c == base_name or c.startswith(f"{base_name}_")]
        if not cols:
            df[base_name] = 0
        else:
            df[base_name] = df[cols].sum(axis=1)
            df.drop(columns=[c for c in cols if c != base_name], inplace=True)
        return df

    weekly = sum_columns(weekly, "fumbles_lost")
    weekly = sum_columns(weekly, "interceptions")
    weekly = sum_columns(weekly, "passing_tds")
    weekly = sum_columns(weekly, "rushing_tds")
    weekly = sum_columns(weekly, "receiving_tds")
    weekly["season"] = season
    weekly["week"] = week

    return weekly