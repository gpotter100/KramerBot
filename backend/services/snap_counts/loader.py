import pandas as pd


def load_snap_counts(season: int, week: int) -> pd.DataFrame:
    """
    Loads snap counts from nflverse player_stats parquet.
    Normalizes schema and safely computes snap_pct.
    """

    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"player_stats/player_stats_{season}.parquet"
    )

    print(f"📡 Loading snap counts for {season} from {url}")
    df = pd.read_parquet(url)

    # Filter to week if available
    if "week" in df.columns:
        df = df[df["week"] == week]

    # Normalize column names
    df.columns = [c.lower() for c in df.columns]

    # Ensure team column exists
    if "recent_team" in df.columns and "team" not in df.columns:
        df = df.rename(columns={"recent_team": "team"})

    # ------------------------------------------------------------
    # Determine which snap columns exist
    # nflverse schemas vary by season
    # ------------------------------------------------------------
    has_pct = "offense_snap_pct" in df.columns
    has_pct2 = "offense_pct" in df.columns
    has_raw = "offense_snaps" in df.columns and "offense_total" in df.columns

    # ------------------------------------------------------------
    # Compute snap_pct safely
    # ------------------------------------------------------------
    if has_pct:
        # Already provided by nflverse
        df = df.rename(columns={"offense_snap_pct": "snap_pct"})
        df["snap_pct"] = df["snap_pct"].fillna(0)

    elif has_pct2:
        # nflverse sometimes uses offense_pct instead
        df = df.rename(columns={"offense_pct": "snap_pct"})
        df["snap_pct"] = df["snap_pct"].fillna(0)

    elif has_raw:
        # Compute snap_pct manually, safely
        df["snap_pct"] = df.apply(
            lambda r: (r["offense_snaps"] / r["offense_total"])
            if r["offense_total"] not in [0, None] else 0,
            axis=1
        )

    else:
        # No snap data at all
        df["snap_pct"] = 0

    # ------------------------------------------------------------
    # Keep only what we need
    # ------------------------------------------------------------
    keep = ["player_id", "player_name", "team", "position", "snap_pct"]
    existing = [c for c in keep if c in df.columns]
    df = df[existing].copy()

    return df
