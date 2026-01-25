import pandas as pd

# ============================================================
#  SAFE NUMERIC ACCESSOR
# ============================================================

def _num(s, default=0):
    try:
        return pd.to_numeric(s, errors="coerce").fillna(default)
    except Exception:
        return default if s is None else float(s)


def coerce_numeric(val, default=0.0):
    try:
        return float(val)
    except Exception:
        return default


# ============================================================
#  SCORING REGISTRY
# ============================================================

SCORING_REGISTRY = {}

def register_scoring(name: str):
    def wrapper(func):
        SCORING_REGISTRY[name] = func
        return func
    return wrapper


# ============================================================
#  BASE COMPONENT BUILDER
# ============================================================

def add_fantasy_components(d: pd.DataFrame) -> pd.DataFrame:
    """
    Adds universal fantasy component fields based on raw stats.
    These are used by ALL scoring systems.
    """

    # Yardage components
    d["comp_passing_yards"]   = _num(d.get("passing_yards", 0))   * 0.04
    d["comp_rushing_yards"]   = _num(d.get("rushing_yards", 0))   * 0.10
    d["comp_receiving_yards"] = _num(d.get("receiving_yards", 0)) * 0.10

    # TD components
    d["comp_passing_tds"]   = _num(d.get("passing_tds", 0))   * 4
    d["comp_rushing_tds"]   = _num(d.get("rushing_tds", 0))   * 6
    d["comp_receiving_tds"] = _num(d.get("receiving_tds", 0)) * 6

    # Turnovers
    d["comp_interceptions"]      = _num(d.get("interceptions", 0))      * -2
    d["comp_fumbles_lost"]       = _num(d.get("fumbles_lost", 0))       * -2
    d["comp_sack_fumbles"]       = _num(d.get("sack_fumbles", 0))       * -2
    d["comp_sack_fumbles_lost"]  = _num(d.get("sack_fumbles_lost", 0))  * -2

    # Receptions (PPR variants override this)
    d["comp_receptions"] = _num(d.get("receptions", 0)) * 0.0

    return d


# ============================================================
#  SCORING SYSTEMS
# ============================================================

@register_scoring("standard")
def score_standard(df: pd.DataFrame) -> pd.DataFrame:
    d = add_fantasy_components(df.copy())

    d["fantasy_points_standard"] = (
        d["comp_passing_yards"]
        + d["comp_rushing_yards"]
        + d["comp_receiving_yards"]
        + d["comp_passing_tds"]
        + d["comp_rushing_tds"]
        + d["comp_receiving_tds"]
        + d["comp_interceptions"]
        + d["comp_fumbles_lost"]
        + d["comp_sack_fumbles"]
        + d["comp_sack_fumbles_lost"]
    )

    return d


@register_scoring("ppr")
def score_ppr(df: pd.DataFrame) -> pd.DataFrame:
    d = score_standard(df)
    d["comp_receptions"] = _num(d.get("receptions", 0)) * 1.0
    d["fantasy_points_ppr"] = d["fantasy_points_standard"] + d["comp_receptions"]
    return d


@register_scoring("half")
def score_half_ppr(df: pd.DataFrame) -> pd.DataFrame:
    d = score_standard(df)
    d["comp_receptions"] = _num(d.get("receptions", 0)) * 0.5
    d["fantasy_points_half"] = d["fantasy_points_standard"] + d["comp_receptions"]
    return d


@register_scoring("vandalay")
def score_vandalay(df: pd.DataFrame) -> pd.DataFrame:
    d = score_half_ppr(df)
    d["fantasy_points_vandalay"] = d["fantasy_points_half"]
    return d


@register_scoring("shen2000")
def score_shen2000(df: pd.DataFrame) -> pd.DataFrame:
    d = score_half_ppr(df)
    d["fantasy_points_shen2000"] = d["fantasy_points_half"]
    return d


# ============================================================
#  PUBLIC API
# ============================================================

def apply_all_scoring(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for name, func in SCORING_REGISTRY.items():
        d = func(d)
    return d


def apply_scoring(df: pd.DataFrame, scoring: str) -> pd.DataFrame:
    scoring = (scoring or "standard").lower()

    d = apply_all_scoring(df)

    if scoring in ["half_ppr", "half-ppr"]:
        scoring = "half"

    col_map = {
        "standard": "fantasy_points_standard",
        "ppr": "fantasy_points_ppr",
        "half": "fantasy_points_half",
        "vandalay": "fantasy_points_vandalay",
        "shen2000": "fantasy_points_shen2000",
    }

    col = col_map.get(scoring, "fantasy_points_standard")
    d["fantasy_points"] = d.get(col, d["fantasy_points_standard"])

    return d


