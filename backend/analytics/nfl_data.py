# analytics/nfl_data.py
"""
nfl_data.py

Core ingestion + access layer for nflverse data via nfl_data_py.

This module is intentionally:
- Read-only
- Cached
- Focused on clean, JSON-ready structures

It’s the foundation for:
- KramerBot visuals (usage, trends, spotlights)
- JARVIS tools (start/sit, projections, matchup analysis)
"""

from functools import lru_cache
from typing import List, Dict, Any, Optional

import pandas as pd
from nfl_data_py import import_weekly_data


# -----------------------------
# Internal helpers
# -----------------------------

@lru_cache(maxsize=16)
def _load_weekly_data_for_season(season: int) -> pd.DataFrame:
    """
    Load all weekly data for a given season from nflverse (via nfl_data_py),
    and cache it in memory for reuse.

    This is the heavy call; everything else filters from here.
    """
    df = import_weekly_data([season])

    # Normalize column names just in case
    df.columns = [c.lower() for c in df.columns]

    return df


def _safe_get(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """
    Return only the columns that exist in the DataFrame.
    This keeps us resilient to schema changes in nflverse.
    """
    existing = [c for c in cols if c in df.columns]
    return df[existing]


# -----------------------------
# Public API
# -----------------------------

def get_weekly_usage(season: int, week: int) -> List[Dict[str, Any]]:
    """
    Return player usage for a given season + week as a list of dicts.

    This is your primary "raw usage" feed:
    - rush attempts
    - targets
    - receptions
    - fantasy points
    - red zone usage (if available)
    """
    df = _load_weekly_data_for_season(season)
    week_df = df[df["week"] == week]

    cols = [
        "player_id",
        "player_name",
        "position",
        "team",
        "opponent_team",
        "season",
        "week",
        "rush_attempts",
        "carries",              # sometimes present
        "targets",
        "receptions",
        "fantasy_points_ppr",
        "red_zone_targets",     # may not always exist
        "red_zone_attempts",    # may not always exist
        "snap_pct",             # if available
        "routes_run",           # if available
    ]

    week_df = _safe_get(week_df, cols)

    # Sort by fantasy points descending as a default view
    if "fantasy_points_ppr" in week_df.columns:
        week_df = week_df.sort_values("fantasy_points_ppr", ascending=False)

    return week_df.to_dict(orient="records")


def get_top_usage(
    season: int,
    week: int,
    position: Optional[str] = None,
    limit: int = 25
) -> List[Dict[str, Any]]:
    """
    Convenience helper: return top usage players for a given week.

    You can filter by position (e.g., "RB", "WR", "TE", "QB") and
    limit the number of players returned.

    This is perfect for:
    - "Top RB usage this week"
    - "Top WR targets this week"
    """
    records = get_weekly_usage(season, week)
    df = pd.DataFrame(records)

    if position:
        df = df[df["position"] == position]

    # Prefer targets + rush attempts as a proxy for usage
    usage_cols = []
    if "targets" in df.columns:
        usage_cols.append("targets")
    if "rush_attempts" in df.columns:
        usage_cols.append("rush_attempts")
    if "carries" in df.columns and "rush_attempts" not in usage_cols:
        usage_cols.append("carries")

    if usage_cols:
        df["usage_score"] = df[usage_cols].sum(axis=1)
        df = df.sort_values("usage_score", ascending=False)
    elif "fantasy_points_ppr" in df.columns:
        df = df.sort_values("fantasy_points_ppr", ascending=False)

    return df.head(limit).to_dict(orient="records")


def get_player_week(
    season: int,
    week: int,
    player_name: str
) -> List[Dict[str, Any]]:
    """
    Return all rows for a given player (by name) in a given week.

    This is handy for:
    - JARVIS answering "How did Bijan do last week?"
    - KramerBot doing quick spotlights
    """
    records = get_weekly_usage(season, week)
    df = pd.DataFrame(records)

    # Case-insensitive match on player_name
    mask = df["player_name"].str.lower() == player_name.lower()
    df = df[mask]

    return df.to_dict(orient="records")
