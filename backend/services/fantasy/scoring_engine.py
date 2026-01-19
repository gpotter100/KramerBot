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


# ============================================================
#  VANDALAY OFFENSE COMPONENTS
# ============================================================

def compute_vandalay_components(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    needed = [
        "passing_yards", "passing_tds", "interceptions",
        "rushing_yards", "rushing_tds",
        "receiving_yards", "receiving_tds", "receptions",
        "two_point_pass", "two_point_rush", "two_point_receive",
        "fumbles_lost",
        "kick_return_tds", "punt_return_tds",
        "off_fumble_recovery_tds",
    ]

    d = coerce_numeric(d, needed)

    for c in needed:
        if c not in d.columns:
            d[c] = 0

    comp = pd.DataFrame(index=d.index)

    comp["passing_yards_pts"] = d["passing_yards"] * 0.04
    comp["passing_tds_pts"] = d["passing_tds"] * 4
    comp["interceptions_pts"] = d["interceptions"] * -2

    comp["rushing_yards_pts"] = d["rushing_yards"] * 0.1
    comp["rushing_tds_pts"] = d["rushing_tds"] * 6

    comp["receiving_yards_pts"] = d["receiving_yards"] * 0.1
    comp["receiving_tds_pts"] = d["receiving_tds"] * 6
    comp["receptions_pts"] = d["receptions"] * 0.5

    comp["two_point_pass_pts"] = d["two_point_pass"] * 2
    comp["two_point_rush_pts"] = d["two_point_rush"] * 2
    comp["two_point_receive_pts"] = d["two_point_receive"] * 2

    comp["fumbles_lost_pts"] = d["fumbles_lost"] * -2

    comp["kick_return_tds_pts"] = d["kick_return_tds"] * 6
    comp["punt_return_tds_pts"] = d["punt_return_tds"] * 6
    comp["off_fumble_recovery_tds_pts"] = d["off_fumble_recovery_tds"] * 6

    # Yardage bonuses
    comp["passing_bonus_pts"] = (
        (d["passing_yards"] >= 300).astype(int) * 3 +
        (d["passing_yards"] >= 350).astype(int) * 1 +
        (d["passing_yards"] >= 400).astype(int) * 1 +
        (d["passing_yards"] >= 450).astype(int) * 1 +
        (d["passing_yards"] >= 500).astype(int) * 1
    )

    comp["receiving_bonus_pts"] = (
        (d["receiving_yards"] >= 100).astype(int) * 3 +
        (d["receiving_yards"] >= 150).astype(int) * 1 +
        (d["receiving_yards"] >= 200).astype(int) * 1 +
        (d["receiving_yards"] >= 250).astype(int) * 1 +
        (d["receiving_yards"] >= 300).astype(int) * 1
    )

    comp["rushing_bonus_pts"] = (
        (d["rushing_yards"] >= 100).astype(int) * 3 +
        (d["rushing_yards"] >= 150).astype(int) * 1 +
        (d["rushing_yards"] >= 200).astype(int) * 1 +
        (d["rushing_yards"] >= 250).astype(int) * 1 +
        (d["rushing_yards"] >= 300).astype(int) * 1
    )

    return comp


# ============================================================
#  VANDALAY DEFENSE COMPONENTS
# ============================================================

def compute_vandalay_defense_components(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    needed = [
        "def_fumble_recoveries",
        "def_interceptions",
        "def_sacks",
        "def_safeties",
        "def_one_point_safety",
        "def_two_point_return",
        "def_tds",
        "def_td_yards",
        "points_allowed",
    ]

    d = coerce_numeric(d, needed)

    for c in needed:
        if c not in d.columns:
            d[c] = 0

    comp = pd.DataFrame(index=d.index)

    comp["fumble_recovery_pts"] = d["def_fumble_recoveries"] * 2
    comp["interceptions_pts"] = d["def_interceptions"] * 2
    comp["sacks_pts"] = d["def_sacks"] * 1
    comp["safety_pts"] = d["def_safeties"] * 2
    comp["one_point_safety_pts"] = d["def_one_point_safety"] * 1
    comp["two_point_return_pts"] = d["def_two_point_return"] * 2

    comp["def_tds_pts"] = d["def_tds"] * 6

    yards = d["def_td_yards"]
    comp["def_td_bonus_pts"] = (
        (yards >= 60).astype(int) * 2 +
        (yards >= 70).astype(int) * 4 +
        (yards >= 80).astype(int) * 6
    )

    pa = d["points_allowed"]
    comp["points_allowed_pts"] = (
        np.where(pa <= 6, 8,
        np.where(pa <= 13, 6,
        np.where(pa <= 20, 4,
        np.where(pa <= 27, 2, 0))))
    )

    return comp


# ============================================================
#  ATTRIBUTION %
# ============================================================

def compute_attribution_percentages(components: pd.DataFrame) -> pd.DataFrame:
    total = components.sum(axis=1)
    total = total.where(total != 0, pd.NA)
    pct = components.div(total, axis=0).fillna(0)
    return pct.add_suffix("_pct")


# ============================================================
#  VANDALAY OFFENSE
# ============================================================

def apply_vandalay_scoring(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(vandalay_points=0)

    comp = compute_vandalay_components(df)
    pct = compute_attribution_percentages(comp)

    out = df.copy()
    out["vandalay_points"] = comp.sum(axis=1)

    return out.join(comp).join(pct)


# ============================================================
#  VANDALAY DEFENSE
# ============================================================

def apply_vandalay_defense(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(vandalay_def_points=0)

    comp = compute_vandalay_defense_components(df)
    pct = compute_attribution_percentages(comp)

    out = df.copy()
    out["vandalay_def_points"] = comp.sum(axis=1)

    return out.join(comp).join(pct)


# ============================================================
#  VANDALAY TOTAL
# ============================================================

def apply_vandalay_total_scoring(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.assign(
            vandalay_points=0,
            vandalay_def_points=0,
            vandalay_total_points=0,
            fantasy_points=0,
            fantasy_points_ppr=0,
            fantasy_points_half=0,
        )

    df = apply_vandalay_scoring(df)
    df = apply_vandalay_defense(df)

    df["vandalay_total_points"] = (
        df.get("vandalay_points", 0) +
        df.get("vandalay_def_points", 0)
    )

    rec = df.get("receptions", 0)

    df["fantasy_points"] = df["vandalay_total_points"]
    df["fantasy_points_ppr"] = df["fantasy_points"] + rec
    df["fantasy_points_half"] = df["fantasy_points"] + 0.5 * rec

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

register_scoring_scheme("vandalay_offense", apply_vandalay_scoring)
register_scoring_scheme("vandalay_defense", apply_vandalay_defense)
register_scoring_scheme("vandalay_total", apply_vandalay_total_scoring)
register_scoring_scheme("standard", apply_standard_scoring)
register_scoring_scheme("shen2000", apply_shen2000_scoring)
