import nfl_data_py as nfl
import pandas as pd

from weekly.normalizer import normalize_weekly_df, empty_weekly_df
from weekly.espn_loader import load_espn_weekly


def load_weekly_data(season: int, week: int) -> pd.DataFrame:
    """
    Loads weekly data for a given season/week.
    - 2002–2024 → nfl_data_py
    - 2025+     → ESPN (placeholder for now)
    """

    # ------------------------------------------------------------
    # Legacy + modern nflverse weekly data (2002–2024)
    # ------------------------------------------------------------
    if season <= 2024:
        try:
            df = nfl.import_weekly_data([season])
            df = df[df["week"] == week]
            return normalize_weekly_df(df)
        except Exception as e:
            print(f"⚠️ nfl_data_py failed for {season} week {week}: {e}")
            return empty_weekly_df()

    # ------------------------------------------------------------
    # ESPN weekly loader (2025+)
    # ------------------------------------------------------------
    try:
        return load_espn_weekly(season, week)
    except Exception as e:
        print(f"⚠️ ESPN weekly loader failed for {season} week {week}: {e}")
        return empty_weekly_df()
