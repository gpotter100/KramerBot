import pandas as pd
import numpy as np
from typing import Callable, Dict

# ============================================================
#  NUMERIC COERCION (critical fix)
# ============================================================

def coerce_numeric(df: pd.DataFrame, cols) -> pd.DataFrame:
    """
    Ensures all scoring-relevant fields are numeric.
    Prevents string arithmetic from silently breaking scoring.
    """
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


# ============================================================
#  SCORING REGISTRY
# ============================================================

SCORING_REGISTRY: Dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {}

def register_scoring_scheme(name: str, func: Callable[[pd.DataFrame], pd.DataFrame]) -> None:
    SCORING_REGISTRY[name] = func

def apply_scoring(df: pd.DataFrame, scheme: str) -> pd.DataFrame:
    """
    Unified scoring entrypoint.
    - Normalizes scheme name
    - Supports aliases (half-ppr, half, etc.)
    - Dispatches to registered scoring functions
    """
    scheme = (scheme or "").lower().strip()

    alias_map = {
        "half-ppr": "half_ppr",
        "half": "half_ppr",
        "0.5ppr": "half_ppr",
        "ppr-half": "half_ppr",
    }

    if scheme in alias_map:
        scheme = alias_map[scheme]

    if scheme not in SCORING_REGISTRY:
        raise ValueError(f"Unknown scoring scheme: {scheme}")

    return SCORING_REGISTRY[scheme](df)


# ============================================================
#  VANDALAY SCORING
# ============================================================

def _num(series, default=0.0):
    """
    Safe numeric converter for pandas Series.
    Assumes caller passes a Series; if None, returns 0-filled Series.
    """
    if series is None:
        return pd.Series(default, index=pd.RangeIndex(0))
    return pd.to_numeric(series, errors="coerce").fillna(default)

def _col(df: pd.DataFrame, name: str, fallback: float = 0.0) -> pd.Series:
    """
    Returns a numeric Series for the given column name.
    If the column is missing, returns a Series of `fallback` with df's index.
    """
    if name in df.columns:
        return _num(df[name], fallback)
    return pd.Series(fallback, index=df.index, dtype=float)

def _col_alt(df: pd.DataFrame, primary: str, alt: str, fallback: float = 0.0) -> pd.Series:
    """
    Returns a numeric Series for primary if present, else alt if present,
    else a fallback Series.
    """
    if primary in df.columns:
        return _num(df[primary], fallback)
    if alt in df.columns:
        return _num(df[alt], fallback)
    return pd.Series(fallback, index=df.index, dtype=float)

def _bonus_tiers(value, tiers):
    """
    tiers: list of (threshold, points) where threshold is inclusive.
    Applied in order; all matching tiers stack.
    """
    pts = 0.0
    for threshold, bonus in tiers:
        if value >= threshold:
            pts += bonus
    return pts

def _vandalay_offense_points(df: pd.DataFrame) -> pd.Series:
    """
    Offensive Vandalay scoring for non-DST players.
    Assumes df has one row per player-week.
    """
    pa_yds = _col(df, "passing_yards", 0)
    pa_tds = _col(df, "passing_tds", 0)
    pa_int = _col_alt(df, "interceptions", "passing_int", 0)
    pa_2pt = _col_alt(df, "passing_two_pt", "pa_two_pt", 0)

    ru_yds = _col(df, "rushing_yards", 0)
    ru_tds = _col(df, "rushing_tds", 0)
    ru_2pt = _col_alt(df, "rushing_two_pt", "ru_two_pt", 0)

    re_yds = _col(df, "receiving_yards", 0)
    re_tds = _col(df, "receiving_tds", 0)
    re_2pt = _col_alt(df, "receiving_two_pt", "re_two_pt", 0)

    rec = _col(df, "receptions", 0)

    fum_lost = _col_alt(df, "fumbles_lost", "fl", 0)

    ikr_td = _col_alt(df, "kick_return_tds", "ikrt_d", 0)
    ipr_td = _col_alt(df, "punt_return_tds", "iprt_d", 0)
    ofr_td = _col_alt(df, "off_fumble_rec_tds", "ofrt_d", 0)
    ifr_td = _col_alt(df, "ind_fumble_rec_tds", "ifrt_d", 0)

    pa_pts = pa_yds * 0.04
    ru_pts = ru_yds * 0.1
    re_pts = re_yds * 0.1

    pa_bonus = pa_yds.apply(
        lambda y: _bonus_tiers(
            y,
            [
                (300, 3),
                (350, 1),
                (400, 1),
                (450, 1),
                (500, 1),
            ],
        )
    )

    ru_bonus = ru_yds.apply(
        lambda y: _bonus_tiers(
            y,
            [
                (100, 3),
                (150, 1),
                (200, 1),
                (250, 1),
                (300, 1),
            ],
        )
    )

    re_bonus = re_yds.apply(
        lambda y: _bonus_tiers(
            y,
            [
                (100, 3),
                (150, 1),
                (200, 1),
                (250, 1),
                (300, 1),
            ],
        )
    )

    td_pts = (
        pa_tds * 4
        + ru_tds * 6
        + re_tds * 6
        + ikr_td * 6
        + ipr_td * 6
        + ofr_td * 6
        + ifr_td * 0
    )

    two_pt_pts = (pa_2pt + ru_2pt + re_2pt) * 2

    rec_pts = rec * 0.5

    turnover_pts = pa_int * -2 + fum_lost * -2

    total_off = (
        pa_pts
        + ru_pts
        + re_pts
        + pa_bonus
        + ru_bonus
        + re_bonus
        + td_pts
        + two_pt_pts
        + rec_pts
        + turnover_pts
    )

    return total_off

def _vandalay_dst_points(df_dst: pd.DataFrame) -> pd.Series:
    """
    Defensive/ST Vandalay scoring for DST rows only.
    df_dst is a subset of df with position == 'DST'.
    """
    sacks = _col_alt(df_dst, "def_sacks", "sacks", 0)
    interceptions = _col_alt(df_dst, "def_interceptions", "def_int", 0)
    fumbles_rec = _col_alt(df_dst, "def_fumbles_recovered", "dfr", 0)
    safeties = _col_alt(df_dst, "safeties", "sty", 0)
    one_pt_safety = _col_alt(df_dst, "one_pt_safety", "sty1pt", 0)
    st_2pt = _col_alt(df_dst, "st_two_pt_returns", "st2pt", 0)

    dtd = _col_alt(df_dst, "def_tds", "dtd", 0)
    dtd_yds = _col_alt(df_dst, "def_td_yards", "dtd_yds", 0)

    points_allowed = _col(df_dst, "points_allowed", 0)
    yards_allowed = _col_alt(df_dst, "yards_allowed", "yds_allowed", 0)

    base_pts = (
        sacks * 1
        + interceptions * 2
        + fumbles_rec * 2
        + safeties * 2
        + one_pt_safety * 1
        + st_2pt * 2
        + dtd * 6
    )

    dtd_bonus = dtd_yds.apply(
        lambda y: _bonus_tiers(
            y,
            [
                (60, 2),
                (70, 4),
                (80, 6),
            ],
        )
    )

    def _points_allowed_tier(pa: float) -> float:
        if pa <= 6:
            return 8
        if pa <= 13:
            return 6
        if pa <= 20:
            return 4
        if pa <= 27:
            return 2
        return 0

    pa_pts = points_allowed.apply(_points_allowed_tier)

    def _yards_allowed_tier(ya: float) -> float:
        if ya <= 49:
            return 12
        if ya <= 99:
            return 10
        if ya <= 149:
            return 8
        if ya <= 199:
            return 6
        if ya <= 249:
            return 4
        if ya <= 299:
            return 2
        return 0

    ya_pts = yards_allowed.apply(_yards_allowed_tier)

    total_def = base_pts + dtd_bonus + pa_pts + ya_pts
    return total_def

def apply_vandalay_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unified Vandalay scoring:
    - Offensive rules for non-DST players
    - Defensive rules ONLY for DST rows
    - Automatically generates a DST row per team if none exist
    - Outputs a single field: fantasy_points
    """
    d = df.copy()

    if "team" not in d.columns:
        raise ValueError("Vandalay scoring requires a 'team' column")

    pos_col = "position" if "position" in d.columns else "pos"
    if pos_col not in d.columns:
        d[pos_col] = ""

    dst_mask = d[pos_col].str.upper() == "DST"
    if not dst_mask.any():
        dst_rows = []
        for team, grp in d.groupby("team"):
            dst_row = {
                "player_name": f"{team} DST",
                "team": team,
                pos_col: "DST",
                "def_sacks": 0,
                "def_interceptions": 0,
                "def_fumbles_recovered": 0,
                "def_tds": 0,
                "def_td_yards": 0,
                "points_allowed": 0,
                "yards_allowed": 0,
            }
            dst_rows.append(dst_row)

        if dst_rows:
            d = pd.concat([d, pd.DataFrame(dst_rows)], ignore_index=True)
            dst_mask = d[pos_col].str.upper() == "DST"

    offense_mask = ~dst_mask
    offense_points = _vandalay_offense_points(d[offense_mask])

    if dst_mask.any():
        dst_points = _vandalay_dst_points(d[dst_mask])
    else:
        dst_points = pd.Series([], dtype=float)

    fantasy_points = pd.Series(0.0, index=d.index)

    fantasy_points.loc[offense_mask] += offense_points.values
    if dst_mask.any():
        fantasy_points.loc[dst_mask] += dst_points.values

    d["fantasy_points"] = fantasy_points

    return d


# ============================================================
#  STANDARD / PPR / HALF-PPR SCORING
# ============================================================

def apply_standard_scoring(df: pd.DataFrame, int_penalty: int = -1) -> pd.DataFrame:
    d = df.copy()

    needed = [
        "passing_yards", "passing_tds", "interceptions",
        "rushing_yards", "rushing_tds",
        "receptions", "receiving_yards", "receiving_tds",
        "two_point_conversions", "fumbles_lost",
        "fumble_recovery_tds",
        "def_sacks", "def_interceptions", "def_fumbles_recovered",
        "def_safeties", "def_tds", "def_return_tds",
        "def_two_point_return", "points_allowed",
        "fg_0_39_made", "fg_40_49_made", "fg_50_plus_made",
        "xp_made", "fg_0_39_missed", "fg_40_49_missed",
    ]

    d = coerce_numeric(d, needed)

    for col in needed:
        if col not in d.columns:
            d[col] = 0

    offense = (
        d["passing_yards"] / 25 +
        d["passing_tds"] * 4 +
        d["interceptions"] * int_penalty +
        d["rushing_yards"] / 10 +
        d["rushing_tds"] * 6 +
        d["receiving_yards"] / 10 +
        d["receiving_tds"] * 6 +
        d["two_point_conversions"] * 2 +
        d["fumble_recovery_tds"] * 6 +
        d["fumbles_lost"] * -2
    )

    pa = d["points_allowed"]
    pa_points = (
        np.where(pa == 0, 10,
        np.where(pa <= 6, 7,
        np.where(pa <= 13, 4,
        np.where(pa <= 20, 1,
        np.where(pa <= 27, 0,
        np.where(pa <= 34, -1, -4))))))  # noqa: E129
    )

    defense = (
        d["def_sacks"] * 1 +
        d["def_interceptions"] * 2 +
        d["def_fumbles_recovered"] * 2 +
        d["def_safeties"] * 2 +
        d["def_tds"] * 6 +
        d["def_return_tds"] * 6 +
        d["def_two_point_return"] * 2 +
        pa_points
    )

    kicking = (
        d["fg_50_plus_made"] * 5 +
        d["fg_40_49_made"] * 4 +
        d["fg_0_39_made"] * 3 +
        d["xp_made"] * 1 +
        d["fg_0_39_missed"] * -2 +
        d["fg_40_49_missed"] * -1
    )

    d["fantasy_points"] = offense + defense + kicking

    rec = d.get("receptions", 0)
    d["fantasy_points_ppr"] = d["fantasy_points"] + rec
    d["fantasy_points_half"] = d["fantasy_points"] + 0.5 * rec

    return d

def apply_ppr_scoring(df: pd.DataFrame) -> pd.DataFrame:
    d = apply_standard_scoring(df)
    d["fantasy_points"] = d["fantasy_points_ppr"]
    return d

def apply_half_ppr_scoring(df: pd.DataFrame) -> pd.DataFrame:
    d = apply_standard_scoring(df)
    d["fantasy_points"] = d["fantasy_points_half"]
    return d


# ============================================================
#  SHEN 2000 SCORING
# ============================================================

def apply_shen2000_scoring(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    needed = [
        "passing_yards", "passing_tds", "interceptions",
        "rushing_yards", "rushing_tds",
        "receptions", "receiving_yards", "receiving_tds",
        "return_tds", "two_point_conversions",
        "fumbles_lost", "off_fumble_recovery_tds",
        "def_sacks", "def_interceptions", "def_fumbles_recovered",
        "def_tds", "def_safeties", "def_block_kicks",
        "def_return_tds", "def_two_point_return",
        "points_allowed",
        "fg_0_19_made", "fg_20_29_made", "fg_30_39_made",
        "fg_40_49_made", "fg_50_plus_made",
        "xp_made",
    ]

    d = coerce_numeric(d, needed)

    for col in needed:
        if col not in d.columns:
            d[col] = 0

    offense = (
        d["passing_yards"] / 25 +
        d["passing_tds"] * 4 +
        d["interceptions"] * -1 +
        d["rushing_yards"] / 10 +
        d["rushing_tds"] * 6 +
        d["receiving_yards"] / 10 +
        d["receiving_tds"] * 6 +
        d["receptions"] * 0.5 +
        d["return_tds"] * 6 +
        d["two_point_conversions"] * 2 +
        d["fumbles_lost"] * -1 +
        d["off_fumble_recovery_tds"] * 6
    )

    pa = d["points_allowed"]
    pa_points = (
        np.where(pa == 0, 10,
        np.where(pa <= 6, 7,
        np.where(pa <= 13, 4,
        np.where(pa <= 20, 1,
        np.where(pa <= 27, 0,
        np.where(pa <= 34, -1, -4))))))  # noqa: E129
    )

    defense = (
        d["def_sacks"] * 1 +
        d["def_interceptions"] * 2 +
        d["def_fumbles_recovered"] * 2 +
        d["def_tds"] * 6 +
        d["def_safeties"] * 2 +
        d["def_block_kicks"] * 2 +
        d["def_return_tds"] * 6 +
        d["def_two_point_return"] * 2 +
        pa_points
    )

    kicking = (
        d["fg_0_19_made"] * 3 +
        d["fg_20_29_made"] * 3 +
        d["fg_30_39_made"] * 3 +
        d["fg_40_49_made"] * 4 +
        d["fg_50_plus_made"] * 5 +
        d["xp_made"] * 1
    )

    d["fantasy_points_shen2000"] = offense + defense + kicking

    rec = d.get("receptions", 0)
    d["fantasy_points"] = d["fantasy_points_shen2000"]
    d["fantasy_points_ppr"] = d["fantasy_points"] + rec
    d["fantasy_points_half"] = d["fantasy_points"] + 0.5 * rec

    return d


# ============================================================
#  REGISTER SCHEMES
# ============================================================

register_scoring_scheme("vandalay", apply_vandalay_scoring)
register_scoring_scheme("standard", apply_standard_scoring)
register_scoring_scheme("ppr", apply_ppr_scoring)
register_scoring_scheme("half_ppr", apply_half_ppr_scoring)
register_scoring_scheme("shen2000", apply_shen2000_scoring)


