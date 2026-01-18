import pandas as pd
import numpy as np


def add_efficiency_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds advanced efficiency metrics to a weekly or usage DataFrame.
    Fully safe against division-by-zero and missing columns.
    """

    if df.empty:
        return df

    d = df.copy()

    # Ensure needed columns exist
    needed = [
        "targets", "receptions", "receiving_yards",
        "carries", "rushing_yards",
        "attempts", "passing_yards", "passing_tds", "interceptions",
        "fantasy_points", "vandalay_points",   # <-- FIXED SPELLING
    ]

    for col in needed:
        if col not in d.columns:
            d[col] = 0

    # Receiving efficiency
    d["yards_per_target"] = d["receiving_yards"] / d["targets"].replace(0, np.nan)
    d["yards_per_target"] = d["yards_per_target"].fillna(0)

    d["yards_per_reception"] = d["receiving_yards"] / d["receptions"].replace(0, np.nan)
    d["yards_per_reception"] = d["yards_per_reception"].fillna(0)

    # Rushing efficiency
    d["yards_per_carry"] = d["rushing_yards"] / d["carries"].replace(0, np.nan)
    d["yards_per_carry"] = d["yards_per_carry"].fillna(0)

    # Passing efficiency
    d["yards_per_attempt"] = d["passing_yards"] / d["attempts"].replace(0, np.nan)
    d["yards_per_attempt"] = d["yards_per_attempt"].fillna(0)

    d["td_rate"] = d["passing_tds"] / d["attempts"].replace(0, np.nan)
    d["td_rate"] = d["td_rate"].fillna(0)

    d["int_rate"] = d["interceptions"] / d["attempts"].replace(0, np.nan)
    d["int_rate"] = d["int_rate"].fillna(0)

    # Fantasy efficiency
    touches = d["carries"] + d["receptions"]
    touches_safe = touches.replace(0, np.nan)

    d["fantasy_per_touch"] = d["fantasy_points"] / touches_safe
    d["fantasy_per_touch"] = d["fantasy_per_touch"].fillna(0)

    d["vandalay_per_touch"] = d["vandalay_points"] / touches_safe
    d["vandalay_per_touch"] = d["vandalay_per_touch"].fillna(0)

    # Role indicators
    d["workhorse_rb"] = ((d["carries"] >= 15) & (d["targets"] >= 4)).astype(int)
    d["alpha_wr"] = (d["targets"] >= 10).astype(int)
    d["deep_threat"] = (d["yards_per_reception"] >= 15).astype(int)

    return d
