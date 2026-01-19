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
    if scheme not in SCORING_REGISTRY:
        raise ValueError(f"Unknown scoring scheme: {scheme}")
    return SCORING_REGISTRY[scheme](df)


# vandalay_scoring.py

import pandas as pd
import numpy as np

# --- helpers ---------------------------------------------------------------

def _num(series, default=0.0):
    if series is None:
        return 0.0
    return pd.to_numeric(series, errors="coerce").fillna(default)

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

# --- offensive scoring -----------------------------------------------------

def _vandalay_offense_points(df: pd.DataFrame) -> pd.Series:
    """
    Offensive Vandalay scoring for non-DST players.
    Assumes df has one row per player-week.
    """

    pa_yds = _num(df.get("passing_yards", 0))
    pa_tds = _num(df.get("passing_tds", 0))
    pa_int = _num(df.get("interceptions", df.get("passing_int", 0)))
    pa_2pt = _num(df.get("passing_two_pt", df.get("pa_two_pt", 0)))

    ru_yds = _num(df.get("rushing_yards", 0))
    ru_tds = _num(df.get("rushing_tds", 0))
    ru_2pt = _num(df.get("rushing_two_pt", df.get("ru_two_pt", 0)))

    re_yds = _num(df.get("receiving_yards", 0))
    re_tds = _num(df.get("receiving_tds", 0))
    re_2pt = _num(df.get("receiving_two_pt", df.get("re_two_pt", 0)))

    rec = _num(df.get("receptions", 0))

    fum_lost = _num(df.get("fumbles_lost", df.get("fl", 0)))

    # Return / fumble recovery TDs (offense / individual)
    ikr_td = _num(df.get("kick_return_tds", df.get("ikrt_d", 0)))
    ipr_td = _num(df.get("punt_return_tds", df.get("iprt_d", 0)))
    ofr_td = _num(df.get("off_fumble_rec_tds", df.get("ofrt_d", 0)))
    ifr_td = _num(df.get("ind_fumble_rec_tds", df.get("ifrt_d", 0)))

    # Base yardage scoring
    pa_pts = pa_yds * 0.04
    ru_pts = ru_yds * 0.1
    re_pts = re_yds * 0.1

    # Yardage bonuses
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

    # TDs and conversions
    td_pts = (
        pa_tds * 4
        + ru_tds * 6
        + re_tds * 6
        + ikr_td * 6
        + ipr_td * 6
        + ofr_td * 6
        + ifr_td * 0  # IFRTD is 0 in your rules
    )

    two_pt_pts = (pa_2pt + ru_2pt + re_2pt) * 2

    # Receptions (fixed 0.5 PPR)
    rec_pts = rec * 0.5

    # Turnovers
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

# --- DST / defensive scoring ----------------------------------------------

def _vandalay_dst_points(df_dst: pd.DataFrame) -> pd.Series:
    """
    Defensive/ST Vandalay scoring for DST rows only.
    df_dst is a subset of df with position == 'DST'.
    """

    sacks = _num(df_dst.get("def_sacks", df_dst.get("sacks", 0)))
    interceptions = _num(df_dst.get("def_interceptions", df_dst.get("def_int", 0)))
    fumbles_rec = _num(df_dst.get("def_fumbles_recovered", df_dst.get("dfr", 0)))
    safeties = _num(df_dst.get("safeties", df_dst.get("sty", 0)))
    one_pt_safety = _num(df_dst.get("one_pt_safety", df_dst.get("sty1pt", 0)))
    st_2pt = _num(df_dst.get("st_two_pt_returns", df_dst.get("st2pt", 0)))

    dtd = _num(df_dst.get("def_tds", df_dst.get("dtd", 0)))
    dtd_yds = _num(df_dst.get("def_td_yards", df_dst.get("dtd_yds", 0)))

    points_allowed = _num(df_dst.get("points_allowed", 0))
    yards_allowed = _num(df_dst.get("yards_allowed", df_dst.get("yds_allowed", 0)))

    # Base DST scoring
    base_pts = (
        sacks * 1
        + interceptions * 2
        + fumbles_rec * 2
        + safeties * 2
        + one_pt_safety * 1
        + st_2pt * 2
        + dtd * 6
    )

    # DTD yardage bonuses
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

    # Points allowed tiers
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

    # Yards allowed tiers
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

# --- main entrypoint -------------------------------------------------------

def apply_vandalay_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """
    Unified Vandalay scoring:
    - Offensive rules for non-DST players
    - Defensive rules ONLY for DST rows
    - Automatically generates a DST row per team if none exist
    - Outputs a single field: fantasy_points
    """

    df = df.copy()

    # Ensure we have a canonical team + position
    if "team" not in df.columns:
        raise ValueError("Vandalay scoring requires a 'team' column")

    pos_col = "position" if "position" in df.columns else "pos"
    if pos_col not in df.columns:
        df[pos_col] = ""

    # --- generate DST rows if none exist -----------------------------------
    dst_mask = df[pos_col].str.upper() == "DST"
    if not dst_mask.any():
        # group by team and synthesize a DST row per team
        dst_rows = []
        for team, grp in df.groupby("team"):
            # if you later add real defensive stats, aggregate them here
            dst_row = {
                "player_name": f"{team} DST",
                "team": team,
                pos_col: "DST",
                # placeholders for defensive stats; safe defaults
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
            df = pd.concat([df, pd.DataFrame(dst_rows)], ignore_index=True)
            dst_mask = df[pos_col].str.upper() == "DST"

    # --- offense scoring for non-DST ---------------------------------------
    offense_mask = ~dst_mask
    offense_points = _vandalay_offense_points(df[offense_mask])

    # --- defense scoring for DST only --------------------------------------
    if dst_mask.any():
        dst_points = _vandalay_dst_points(df[dst_mask])
    else:
        dst_points = pd.Series([], dtype=float)

    # --- combine into fantasy_points ---------------------------------------
    fantasy_points = pd.Series(0.0, index=df.index)

    fantasy_points.loc[offense_mask] += offense_points.values
    if dst_mask.any():
        fantasy_points.loc[dst_mask] += dst_points.values

    df["fantasy_points"] = fantasy_points

    return df


# ============================================================
#  STANDARD SCORING
# ============================================================

def apply_standard_scoring(df: pd.DataFrame, int_penalty=-1) -> pd.DataFrame:
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
        np.where(pa <= 34, -1, -4))))))
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
        np.where(pa <= 34, -1, -4))))))
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
register_scoring_scheme("shen2000", apply_shen2000_scoring)
