import pandas as pd
import numpy as np


def add_efficiency_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds advanced efficiency metrics to a weekly or usage DataFrame.
    """

    if df.empty:
        return df

    d = df.copy()

    # Ensure needed columns exist
    for col in [
        "targets", "receptions", "receiving_yards",
        "carries", "rushing_yards",
        "attempts", "passing_yards", "passing_tds", "interceptions",
        "fantasy_points", "vandalary_points",
    ]:
        if col not in d.columns:
            d[col] = 0

    # Receiving efficiency
    d["yards_per_target"] = np.where(d["targets"] > 0, d["receiving_yards"] / d["targets"], 0)
    d["yards_per_reception"] = np.where(d["receptions"] > 0, d["receiving_yards"] / d["receptions"], 0)

    # Rushing efficiency
    d["yards_per_carry"] = np.where(d["carries"] > 0, d["rushing_yards"] / d["carries"], 0)

    # Passing efficiency
    d["yards_per_attempt"] = np.where(d["attempts"] > 0, d["passing_yards"] / d["attempts"], 0)
    d["td_rate"] = np.where(d["attempts"] > 0, d["passing_tds"] / d["attempts"], 0)
    d["int_rate"] = np.where(d["attempts"] > 0, d["interceptions"] / d["attempts"], 0)

    # Fantasy efficiency
    touches = d["carries"] + d["receptions"]
    d["fantasy_per_touch"] = np.where(touches > 0, d["fantasy_points"] / touches, 0)
    d["vandalary_per_touch"] = np.where(touches > 0, d["vandalary_points"] / touches, 0)

    # Role indicators
    d["workhorse_rb"] = np.where((d["carries"] >= 15) & (d["targets"] >= 4), 1, 0)
    d["alpha_wr"] = np.where(d["targets"] >= 10, 1, 0)
    d["deep_threat"] = np.where(d["yards_per_reception"] >= 15, 1, 0)

    return d
