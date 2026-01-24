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
    """
    Backward-compatible helper for older loaders.
    Converts a value to float, returns default on failure.
    """
    try:
        return float(val)
    except Exception:
        return default


# ============================================================
#  SCORING REGISTRY
# ============================================================

SCORING_REGISTRY = {}


def register_scoring(name: str):
    """
    Decorator to register a scoring system.
    name: 'standard', 'ppr', 'half', 'vandalay', 'shen2000', etc.
    """
    def wrapper(func):
        SCORING_REGISTRY[name] = func
        return func
    return wrapper


# ============================================================
#  SCORING SYSTEMS
# ============================================================

@register_scoring("standard")
def score_standard(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standard scoring:
    - 0.04 per passing yard
    - 0.1 per rushing/receiving yard
    - 4 per passing TD
    - 6 per rushing/receiving TD
    - -2 per interception
    - -2 per fumble lost
    - 0 per reception
    """
    d = df.copy()

    pass_yds = _num(d.get("passing_yards", 0))
    rush_yds = _num(d.get("rushing_yards", 0))
    rec_yds = _num(d.get("receiving_yards", 0))

    pass_tds = _num(d.get("passing_tds", 0))
    rush_tds = _num(d.get("rushing_tds", 0))
    rec_tds = _num(d.get("receiving_tds", 0))

    ints = _num(d.get("interceptions", 0))
    fumbles = _num(d.get("fumbles_lost", 0))

    d["fantasy_points_standard"] = (
        pass_yds * 0.04
        + rush_yds * 0.1
        + rec_yds * 0.1
        + pass_tds * 4
        + rush_tds * 6
        + rec_tds * 6
        - ints * 2
        - fumbles * 2
    )

    return d


@register_scoring("ppr")
def score_ppr(df: pd.DataFrame) -> pd.DataFrame:
    """
    PPR scoring: standard + 1.0 per reception.
    """
    d = score_standard(df)
    rec = _num(d.get("receptions", 0))

    d["fantasy_points_ppr"] = d["fantasy_points_standard"] + rec * 1.0
    return d


@register_scoring("half")
def score_half_ppr(df: pd.DataFrame) -> pd.DataFrame:
    """
    Half-PPR scoring: standard + 0.5 per reception.
    """
    d = score_standard(df)
    rec = _num(d.get("receptions", 0))

    d["fantasy_points_half"] = d["fantasy_points_standard"] + rec * 0.5
    return d


@register_scoring("vandalay")
def score_vandalay(df: pd.DataFrame) -> pd.DataFrame:
    """
    Vandalay scoring:
    For now: same as Half-PPR (you can customize later).
    """
    d = score_half_ppr(df)
    d["fantasy_points_vandalay"] = d["fantasy_points_half"]
    return d


@register_scoring("shen2000")
def score_shen2000(df: pd.DataFrame) -> pd.DataFrame:
    """
    SHEN2000 scoring:
    For now: same as Half-PPR (you can customize later).
    """
    d = score_half_ppr(df)
    d["fantasy_points_shen2000"] = d["fantasy_points_half"]
    return d


# ============================================================
#  PUBLIC API
# ============================================================

def apply_all_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply ALL registered scoring systems to the DataFrame.
    Produces columns:
      - fantasy_points_standard
      - fantasy_points_ppr
      - fantasy_points_half
      - fantasy_points_vandalay
      - fantasy_points_shen2000
    (plus any future ones you register).
    """
    d = df.copy()
    for name, func in SCORING_REGISTRY.items():
        d = func(d)
    return d


def apply_scoring(df: pd.DataFrame, scoring: str) -> pd.DataFrame:
    """
    Compute all scoring systems, then set 'fantasy_points'
    to the selected scoring system.
    """
    scoring = (scoring or "standard").lower()

    d = apply_all_scoring(df)

    # Map aliases
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
    if col not in d.columns:
        # Fallback to standard if something is off
        col = "fantasy_points_standard"

    d["fantasy_points"] = d[col]

    return d


