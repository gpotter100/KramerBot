import pandas as pd
from weekly.normalizer import empty_weekly_df

def load_espn_weekly(season: int, week: int) -> pd.DataFrame:
    """
    Placeholder ESPN weekly loader.
    Returns an empty normalized weekly DataFrame until ESPN parsing is implemented.
    """
    print(f"⚠️ ESPN weekly loader not implemented for {season} week {week}. Returning empty.")
    return empty_weekly_df()
