import pandas as pd
import numpy as np

# ============================================================
#  SAFE NUMERIC ACCESSORS
# ============================================================

def _num(df, col, default=0.0):
    """Return numeric column or fallback series."""
    if col in df.columns:
        return pd.to_numeric(df[col], errors="coerce").fillna(default)
    return pd.Series(default, index=df.index, dtype=float)


# ============================================================
#  RAW COMPONENT EXTRACTION
# ============================================================

def compute_raw_components(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts raw fantasy components from weekly or multi-week usage rows.
    Produces additive components that sum to fantasy_points (for the
    selected scoring system).
    """

    d = df.copy()

    # Yardage components
    d["comp_passing_yards"] = _num(d, "passing_yards") * 0.04
    d["comp_rushing_yards"] = _num(d, "rushing_yards") * 0.1
    d["comp_receiving_yards"] = _num(d, "receiving_yards") * 0.1

    # TD components
    d["comp_passing_tds"] = _num(d, "passing_tds") * 4
    d["comp_rushing_tds"] = _num(d, "rushing_tds") * 6
    d["comp_receiving_tds"] = _num(d, "receiving_tds") * 6

    # Reception component (PPR / half-PPR handled later)
    d["comp_receptions"] = _num(d, "receptions") * 0.5  # base half-PPR

    # Turnovers
    d["comp_interceptions"] = _num(d, "interceptions") * -2
    d["comp_fumbles_lost"] = _num(d, "fumbles_lost") * -2

    # Bonuses (yardage tiers)
    def bonus_tiers(yards, tiers):
        pts = 0.0
        for threshold, bonus in tiers:
            if yards >= threshold:
                pts += bonus
        return pts

    d["comp_bonus_passing"] = _num(d, "passing_yards").apply(
        lambda y: bonus_tiers(y, [(300, 3), (350, 1), (400, 1), (450, 1), (500, 1)])
    )

    d["comp_bonus_rushing"] = _num(d, "rushing_yards").apply(
        lambda y: bonus_tiers(y, [(100, 3), (150, 1), (200, 1), (250, 1), (300, 1)])
    )

    d["comp_bonus_receiving"] = _num(d, "receiving_yards").apply(
        lambda y: bonus_tiers(y, [(100, 3), (150, 1), (200, 1), (250, 1), (300, 1)])
    )

    return d


# ============================================================
#  APPLY SCORING ADJUSTMENTS
# ============================================================

def apply_scoring_adjustments(df: pd.DataFrame, scoring: str) -> pd.DataFrame:
    """
    Adjusts attribution components based on scoring system.
    - Standard: receptions = 0
    - PPR: receptions = 1.0 per rec
    - Half-PPR: receptions = 0.5 per rec
    - Vandalay: receptions = 0.5 per rec
    - SHEN2000: receptions = 0.5 per rec
    """

    d = df.copy()
    scoring = (scoring or "standard").lower()

    if scoring == "standard":
        d["comp_receptions"] = 0

    elif scoring == "ppr":
        d["comp_receptions"] = _num(d, "receptions") * 1.0

    elif scoring in ["half", "half_ppr", "half-ppr", "vandalay", "shen2000"]:
        d["comp_receptions"] = _num(d, "receptions") * 0.5

    return d


# ============================================================
#  PERCENTAGE ATTRIBUTION
# ============================================================

ATTR_COLUMNS = [
    "comp_passing_yards",
    "comp_rushing_yards",
    "comp_receiving_yards",
    "comp_passing_tds",
    "comp_rushing_tds",
    "comp_receiving_tds",
    "comp_receptions",
    "comp_interceptions",
    "comp_fumbles_lost",
    "comp_bonus_passing",
    "comp_bonus_rushing",
    "comp_bonus_receiving",
]

def compute_percentages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts raw components into percentages of fantasy_points
    (for the selected scoring system).
    """

    d = df.copy()

    total_fp = _num(d, "fantasy_points", 0.0001)  # avoid divide-by-zero

    for col in ATTR_COLUMNS:
        pct_col = col.replace("comp_", "pct_")
        d[pct_col] = (d[col] / total_fp) * 100

    return d


# ============================================================
#  PUBLIC ENTRYPOINT
# ============================================================

def compute_fantasy_attribution(df: pd.DataFrame, scoring: str) -> pd.DataFrame:
    """
    Full attribution pipeline:
    1. Extract raw components
    2. Apply scoring adjustments
    3. Compute percentages
    4. Produce clean 'attr' dict per row
    """

    d = compute_raw_components(df)
    d = apply_scoring_adjustments(d, scoring)
    d = compute_percentages(d)

    # Build final attribution dict
    attr_dicts = []
    for _, row in d.iterrows():
        attr = {}
        for col in ATTR_COLUMNS:
            pct_col = col.replace("comp_", "pct_")
            clean_key = col.replace("comp_", "")
            attr[clean_key] = {
                "raw": float(row[col]),
                "pct": float(row[pct_col]),
            }
        attr_dicts.append(attr)

    d["attr"] = attr_dicts
    return d
