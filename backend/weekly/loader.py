import pandas as pd

from services.loaders.pbp_weekly_loader import load_weekly_from_pbp
from services.loaders.id_harmonizer import harmonize_ids
from weekly.normalizer import empty_weekly_df  # optional, if you still want it
from weekly.normalizer import normalize_weekly_df  # optional, may be removed later
from weekly.usage import aggregate_player_usage


def load_weekly_data(season: int, week: int) -> pd.DataFrame:
    """
    Unified weekly loader:
    Always load weekly usage from local PBP parquet via the weekly builder.
    """

    print(f"🔥 Weekly loader: loading {season} week {week} from local PBP")

    # Step 1 — Load weekly plays from local PBP parquet
    df = load_weekly_from_pbp(season, week)

    if df.empty:
        print(f"⚠️ No weekly data for {season} week {week}")
        return empty_weekly_df()

    # Step 2 — Load rosters for ID harmonization
    from routers.nfl_router import load_rosters  # avoid circular import
    rosters = load_rosters(season)

    # Step 3 — Harmonize IDs (team, player_id, position)
    df = harmonize_ids(df, rosters)

    # Step 4 — Normalize (optional, depending on your schema)
    df = normalize_weekly_df(df)

    # Step 5 — Aggregate into player-level usage
    df = aggregate_player_usage(df)

    return df
