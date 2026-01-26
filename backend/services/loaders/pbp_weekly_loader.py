import pandas as pd
import polars as pl
from pathlib import Path

from services.nfl_pbp_service import pbp_week

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
    # Load the parquet
    local_path = LOCAL_PBP_DIR / f"pbp_{season}.parquet"

    # Debug: print schema
    pbp_week = pd.read_parquet(local_path)
    print(f"DEBUG: Loaded PBP for {season} week {week}")
    print("PBP COLUMNS:", pbp_week.columns.tolist())

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

    # Identify receiver column
    if "receiver_player_id" in rec_events.columns:
        rec_col = "receiver_player_id"
    elif "receiver_id" in rec_events.columns:
        rec_col = "receiver_id"
    else:
        rec_col = None
    # Receiving TDs
    if rec_col:
        rec_td_events = rec_events[
            (rec_events.get("receiving_tds", 0) == 1) &
            (rec_events[rec_col].notna())
        ]
    else:
        rec_td_events = rec_events.iloc[0:0]

    # Identify fumble_lost column
    if "fumble_lost" in rec_events.columns:
        fumble_lost_col = "fumble_lost"
    else:
        fumble_lost_col = None
    # Receiving fumbles lost
    if rec_col and fumble_lost_col:
        rec_fumble_lost_events = rec_events[
            (rec_events[fumble_lost_col] == 1) &
            (rec_events[rec_col].notna())
        ]
    else:
        rec_fumble_lost_events = rec_events.iloc[0:0]
    # Build receiving dataframe
    rec_df = (
        rec_events.groupby([rec_col, "receiver", "posteam"], dropna=True)
        .agg(
            targets=(rec_col, "count"),
            receptions=("complete_pass", "sum"),
            receiving_yards=("yards_gained", "sum"),
            receiving_air_yards=("air_yards", "sum"),
            receiving_first_downs=("first_down", "sum"),
            receiving_epa=("epa", "sum"),
            receiving_tds=(rec_col, lambda x: x.isin(rec_td_events[rec_col]).sum()),
            fumbles_lost=(rec_col, lambda x: x.isin(rec_fumble_lost_events[rec_col]).sum()),
        )
        .reset_index()
        .rename(columns={
            rec_col: "player_id",
            "receiver": "player_name",
            "posteam": "team"
        })
    )


    # ------------------------------------------------------------
    # RUSHING
    # ------------------------------------------------------------

    rush_events = pbp_week[pbp_week.get("rush_attempt", 0) == 1]

    # Identify rusher column
    if "rusher_player_id" in rush_events.columns:
        rusher_col = "rusher_player_id"
    elif "rusher_id" in rush_events.columns:
        rusher_col = "rusher_id"
    else:
        rusher_col = None
    # Rushing TDs
    if rusher_col:
        rush_td_events = rush_events[
            (rush_events.get("rushing_tds", 0) == 1) &
            (rush_events[rusher_col].notna())
        ]
    else:
        rush_td_events = rush_events.iloc[0:0]

    # Identify fumble_lost column
    if "fumble_lost" in rush_events.columns:
        fumble_lost_col = "fumble_lost"
    else:
        fumble_lost_col = None
    # Rushing fumbles lost
    if rusher_col and fumble_lost_col:
        rush_fumble_lost_events = rush_events[
            (rush_events[fumble_lost_col] == 1) &
            (rush_events[rusher_col].notna())
        ]
    else:
        rush_fumble_lost_events = rush_events.iloc[0:0]

    # Build rushing dataframe
    rush_df = (
        rush_events.groupby([rusher_col, "rusher", "posteam"], dropna=True)
        .agg(
            carries=(rusher_col, "count"),
            rushing_yards=("yards_gained", "sum"),
            rushing_epa=("epa", "sum"),
            rushing_tds=(rusher_col, lambda x: x.isin(rush_td_events[rusher_col]).sum()),
            fumbles_lost=(rusher_col, lambda x: x.isin(rush_fumble_lost_events[rusher_col]).sum()),
        )
        .reset_index()
        .rename(columns={
            rusher_col: "player_id",
            "rusher": "player_name",
            "posteam": "team"
        })
    )

    # ------------------------------------------------------------
    # PASSING
    # ------------------------------------------------------------

    # TRUE pass plays only
    pass_events = pbp_week[pbp_week["play_type"] == "pass"]
    # Passing TDs
    pass_td_events = pass_events[
        (pass_events["touchdown"] == 1) &
        (pass_events["desc"].str.contains("pass", case=False, na=False)) &
        (pass_events["receiver_id"].notna()) &
        (pass_events["passer_id"].notna())
    ]

    # Interceptions
    int_events = pass_events[
        (pass_events["interception"] == 1) &
        (pass_events["desc"].str.contains("intercept", case=False, na=False)) &
        (pass_events["passer_id"].notna())
    ]

    # Sack fumbles lost
    sack_fumble_lost_events = pass_events[
        (pass_events["fumble_lost"] == 1) &
        (pass_events["desc"].str.contains("sack", case=False, na=False)) &
        (pass_events["passer_id"].notna())
    ]

    # Sack fumbles = sack fumbles lost (no separate fumble column)
    sack_fumble_events = sack_fumble_lost_events

    # ------------------------------------------------------------
    # Count events by passer_id (THIS is the fix)
    # ------------------------------------------------------------

    td_counts = pass_td_events.groupby("passer_id").size().rename("passing_tds")
    int_counts = int_events.groupby("passer_id").size().rename("interceptions")
    sack_f_counts = sack_fumble_events.groupby("passer_id").size().rename("sack_fumbles")
    sack_f_lost_counts = sack_fumble_lost_events.groupby("passer_id").size().rename("sack_fumbles_lost")

    # ------------------------------------------------------------
    # Base passing stats
    # ------------------------------------------------------------

    pass_df = (
        pass_events.groupby(["passer_id", "passer", "posteam"], dropna=True)
        .agg(
            attempts=("pass_attempt", "sum"),
            completions=("complete_pass", "sum"),
            passing_yards=("yards_gained", "sum"),
            passing_air_yards=("air_yards", "sum"),
            passing_first_downs=("first_down", "sum"),
            passing_epa=("epa", "sum"),
        )
        .reset_index()
    )

    # ------------------------------------------------------------
    # Merge event counts
    # ------------------------------------------------------------

    pass_df = (
        pass_df
        .merge(td_counts, on="passer_id", how="left")
        .merge(int_counts, on="passer_id", how="left")
        .merge(sack_f_counts, on="passer_id", how="left")
        .merge(sack_f_lost_counts, on="passer_id", how="left")
        .fillna(0)
    )

    # ------------------------------------------------------------
    # Final rename
    # ------------------------------------------------------------

    pass_df = pass_df.rename(columns={
        "passer_id": "player_id",
        "passer": "player_name",
        "posteam": "team"
    })

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