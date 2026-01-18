import pandas as pd


def load_snap_counts(season: int, week: int) -> pd.DataFrame:
    """
    Loads snap counts from nflverse (for now).
    Later this can be ingested locally like PBP.
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

    # Keep only what we need
    cols = ["player_id", "player_name", "recent_team", "position", "offense_snaps", "offense_snap_pct"]
    existing = [c for c in cols if c in df.columns]
    df = df[existing].copy()

    if "recent_team" in df.columns and "team" not in df.columns:
        df = df.rename(columns={"recent_team": "team"})

    if "offense_snap_pct" in df.columns and "snap_pct" not in df.columns:
        df = df.rename(columns={"offense_snap_pct": "snap_pct"})

    return df
