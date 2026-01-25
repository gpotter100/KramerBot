import pandas as pd

def compute_fantasy_attribution(df: pd.DataFrame, scoring: str) -> pd.DataFrame:
    """
    Adds fantasy component attribution percentages for the selected scoring system.
    Requires that scoring_engine has already added all comp_* fields.
    """

    d = df.copy()

    # Determine which fantasy_points_* column is active
    scoring = (scoring or "standard").lower()
    if scoring in ["half_ppr", "half-ppr"]:
        scoring = "half"

    col_map = {
        "standard": "fantasy_points_standard",
        "ppr": "fantasy_points_ppr",
        "half": "fantasy_points_half",
        "vandalay": "fantasy_points_vandalay",
        "shen2000": "fantasy_points_shen2000",
    }

    fp_col = col_map.get(scoring, "fantasy_points_standard")
    d["fantasy_points_active"] = d.get(fp_col, d["fantasy_points_standard"])

    # Avoid division by zero
    total = d["fantasy_points_active"].replace(0, 1e-9)

    # Yardage attribution
    d["pct_passing_yards"]   = d["comp_passing_yards"]   / total
    d["pct_rushing_yards"]   = d["comp_rushing_yards"]   / total
    d["pct_receiving_yards"] = d["comp_receiving_yards"] / total

    # Touchdown attribution
    d["pct_passing_tds"]   = d["comp_passing_tds"]   / total
    d["pct_rushing_tds"]   = d["comp_rushing_tds"]   / total
    d["pct_receiving_tds"] = d["comp_receiving_tds"] / total

    # Turnover attribution
    d["pct_interceptions"]      = d["comp_interceptions"]      / total
    d["pct_fumbles_lost"]       = d["comp_fumbles_lost"]       / total
    d["pct_sack_fumbles"]       = d["comp_sack_fumbles"]       / total
    d["pct_sack_fumbles_lost"]  = d["comp_sack_fumbles_lost"]  / total

    # Reception attribution (PPR / Half-PPR)
    d["pct_receptions"] = d["comp_receptions"] / total

    # Total attribution sanity check
    d["pct_total"] = (
        d["pct_passing_yards"]
        + d["pct_rushing_yards"]
        + d["pct_receiving_yards"]
        + d["pct_passing_tds"]
        + d["pct_rushing_tds"]
        + d["pct_receiving_tds"]
        + d["pct_interceptions"]
        + d["pct_fumbles_lost"]
        + d["pct_sack_fumbles"]
        + d["pct_sack_fumbles_lost"]
        + d["pct_receptions"]
    )

    return d
