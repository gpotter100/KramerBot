import pandas as pd
import numpy as np
from typing import Callable, Dict


# ============================================================
#  SCORING REGISTRY (single source of truth)
# ============================================================

SCORING_REGISTRY: Dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {}


def register_scoring_scheme(name: str, func: Callable[[pd.DataFrame], pd.DataFrame]) -> None:
    """
    Register a custom scoring scheme at runtime.
    """
    SCORING_REGISTRY[name] = func


def apply_scoring(df: pd.DataFrame, scheme: str) -> pd.DataFrame:
    """
    Apply a named scoring scheme to a weekly DataFrame.
    """
    if scheme not in SCORING_REGISTRY:
        raise ValueError(f"Unknown scoring scheme: {scheme}")
    return SCORING_REGISTRY[scheme](df)


# ============================================================
#  VANDALAY OFFENSE — COMPONENTS
# ============================================================

def compute_vandalay_components(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with per-category fantasy point components
    for Vandalay offensive scoring.
    """

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
    for c in needed:
        if c not in d.columns:
            d[c] = 0

    comp = pd.DataFrame(index=d.index)

    # Base scoring
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
#  VANDALAY DEFENSE — COMPONENTS
# ============================================================

def compute_vandalay_defense_components(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes defensive fantasy point components for Vandalay Scoring.
    """

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

    # TD yardage bonuses
    yards = d["def_td_yards"]
    comp["def_td_bonus_pts"] = (
        (yards >= 60).astype(int) * 2 +
        (yards >= 70).astype(int) * 4 +
        (yards >= 80).astype(int) * 6
    )

    # Points allowed tiers
    pa = d["points_allowed"]
    comp["points_allowed_pts"] = (
        np.where(pa <= 6, 8,
        np.where(pa <= 13, 6,
        np.where(pa <= 20, 4,
        np.where(pa <= 27, 2, 0))))
    )

    return comp


# ============================================================
#  ATTRIBUTION % — SAFE VERSION
# ============================================================

def compute_attribution_percentages(components: pd.DataFrame) -> pd.DataFrame:
    """
    Computes attribution percentages safely, avoiding division-by-zero
    and Pandas downcasting warnings.
    """
    total = components.sum(axis=1)

    # Replace 0 totals with NA to avoid division-by-zero
    total = total.where(total != 0, pd.NA)

    pct = components.div(total, axis=0)
    pct = pct.fillna(0)

    return pct.add_suffix("_pct")


# ============================================================
#  APPLY SCORING — OFFENSE
# ============================================================

def apply_vandalay_scoring(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["vandalay_points"] = []
        return df

    comp = compute_vandalay_components(df)
    pct = compute_attribution_percentages(comp)

    df = df.copy()
    df["vandalay_points"] = comp.sum(axis=1)

    return df.join(comp).join(pct)


# ============================================================
#  APPLY SCORING — DEFENSE
# ============================================================

def apply_vandalay_defense(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["vandalay_def_points"] = []
        return df

    comp = compute_vandalay_defense_components(df)
    pct = compute_attribution_percentages(comp)

    df = df.copy()
    df["vandalay_def_points"] = comp.sum(axis=1)

    return df.join(comp).join(pct)


# ============================================================
#  APPLY SCORING — TOTAL (OFFENSE + DEFENSE)
# ============================================================

def apply_vandalay_total_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """
    Combines offense + defense Vandalay scoring.
    """
    df = apply_vandalay_scoring(df)
    df = apply_vandalay_defense(df)

    df["vandalay_total_points"] = (
        df.get("vandalay_points", 0) +
        df.get("vandalay_def_points", 0)
    )

    return df

def apply_standard_scoring(df: pd.DataFrame, int_penalty=-1) -> pd.DataFrame:
    """
    Applies your Standard Fantasy Scoring system.
    Produces:
      - fantasy_points
      - fantasy_points_ppr
      - fantasy_points_half
    """

    d = df.copy()

    # Ensure missing fields exist
    needed = [
        "passing_yards", "passing_tds", "interceptions",
        "rushing_yards", "rushing_tds",
        "receptions", "receiving_yards", "receiving_tds",
        "two_point_conversions", "fumbles_lost",
        "fumble_recovery_tds",

        # Defense
        "def_sacks", "def_interceptions", "def_fumbles_recovered",
        "def_safeties", "def_tds", "def_return_tds",
        "def_two_point_return", "points_allowed",

        # Kicking
        "fg_0_39_made", "fg_40_49_made", "fg_50_plus_made",
        "xp_made", "fg_0_39_missed", "fg_40_49_missed",
    ]

    for col in needed:
        if col not in d.columns:
            d[col] = 0

    # ------------------------------
    # OFFENSE
    # ------------------------------
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

    # ------------------------------
    # DEFENSE / SPECIAL TEAMS
    # ------------------------------
    pa = d["points_allowed"]

    pa_points = (
        np.where(pa == 0, 10,
        np.where(pa <= 6, 7,
        np.where(pa <= 13, 4,
        np.where(pa <= 20, 1,
        np.where(pa <= 27, 0,
        np.where(pa <= 34, -1, -4)))))))
    

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

    # ------------------------------
    # KICKERS
    # ------------------------------
    kicking = (
        d["fg_50_plus_made"] * 5 +
        d["fg_40_49_made"] * 4 +
        d["fg_0_39_made"] * 3 +
        d["xp_made"] * 1 +
        d["fg_0_39_missed"] * -2 +
        d["fg_40_49_missed"] * -1
    )

    # ------------------------------
    # TOTAL STANDARD FANTASY POINTS
    # ------------------------------
    d["fantasy_points"] = offense + defense + kicking

    # ------------------------------
    # PPR VARIANTS
    # ------------------------------
    d["fantasy_points_ppr"] = d["fantasy_points"] + d["receptions"]
    d["fantasy_points_half"] = d["fantasy_points"] + 0.5 * d["receptions"]

    return d


def apply_shen2000_scoring(df: pd.DataFrame) -> pd.DataFrame:
    """
    SHEN 2000 Scoring System
    - 0.5 PPR
    - Yahoo-style offense, defense, and kicking
    """

    d = df.copy()

    # Ensure missing fields exist
    needed = [
        # Offense
        "passing_yards", "passing_tds", "interceptions",
        "rushing_yards", "rushing_tds",
        "receptions", "receiving_yards", "receiving_tds",
        "return_tds", "two_point_conversions",
        "fumbles_lost", "off_fumble_recovery_tds",

        # Defense
        "def_sacks", "def_interceptions", "def_fumbles_recovered",
        "def_tds", "def_safeties", "def_block_kicks",
        "def_return_tds", "def_two_point_return",
        "points_allowed",

        # Kicking
        "fg_0_19_made", "fg_20_29_made", "fg_30_39_made",
        "fg_40_49_made", "fg_50_plus_made",
        "xp_made",
    ]

    for col in needed:
        if col not in d.columns:
            d[col] = 0

    # ------------------------------
    # OFFENSE
    # ------------------------------
    offense = (
        d["passing_yards"] / 25 +
        d["passing_tds"] * 4 +
        d["interceptions"] * -1 +
        d["rushing_yards"] / 10 +
        d["rushing_tds"] * 6 +
        d["receiving_yards"] / 10 +
        d["receiving_tds"] * 6 +
        d["receptions"] * 0.5 +  # SHEN 2000 is 0.5 PPR
        d["return_tds"] * 6 +
        d["two_point_conversions"] * 2 +
        d["fumbles_lost"] * -1 +  # SHEN uses -1, not -2
        d["off_fumble_recovery_tds"] * 6
    )

    # ------------------------------
    # DEFENSE / SPECIAL TEAMS
    # ------------------------------
    pa = d["points_allowed"]

    pa_points = (
        np.where(pa == 0, 10,
        np.where(pa <= 6, 7,
        np.where(pa <= 13, 4,
        np.where(pa <= 20, 1,
        np.where(pa <= 27, 0,
        np.where(pa <= 34, -1, -4)))))))
    

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

    # ------------------------------
    # KICKERS
    # ------------------------------
    kicking = (
        d["fg_0_19_made"] * 3 +
        d["fg_20_29_made"] * 3 +
        d["fg_30_39_made"] * 3 +
        d["fg_40_49_made"] * 4 +
        d["fg_50_plus_made"] * 5 +
        d["xp_made"] * 1
    )

    # ------------------------------
    # TOTAL SHEN 2000 FANTASY POINTS
    # ------------------------------
    d["fantasy_points_shen2000"] = offense + defense + kicking

    
    
    return d


# ============================================================
#  REGISTER SCHEMES
# ============================================================

register_scoring_scheme("vandalay_offense", apply_vandalay_scoring)
register_scoring_scheme("vandalay_defense", apply_vandalay_defense)
register_scoring_scheme("vandalay_total", apply_vandalay_total_scoring)
register_scoring_scheme("standard", apply_standard_scoring)
register_scoring_scheme("shen2000", apply_shen2000_scoring)
