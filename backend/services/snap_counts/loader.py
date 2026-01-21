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
            lambda r: (r["offense_snaps"] / r["offense_total"]) if r["offense_total"] not in [0, None] else 0,
            axis=1,
        )

    else:
        # Try to derive snap_pct from local PBP if available (approximate)
        try:
            import polars as pl
            from services.loaders.pbp_weekly_loader import load_pbp_local

            lf = load_pbp_local(season)
            lf_week = lf.filter(pl.col("week") == week)
            pbp_df = lf_week.collect().to_pandas()
        except Exception:
            pbp_df = None

        if pbp_df is not None and not pbp_df.empty:
            team_plays = pbp_df.groupby("posteam").size().to_dict()

            def player_play_count(pid, team):
                if pid is None:
                    return 0
                mask = (
                    (pbp_df.get("posteam") == team)
                    & (
                        (pbp_df.get("rusher_id") == pid)
                        | (pbp_df.get("passer_id") == pid)
                        | (pbp_df.get("receiver_id") == pid)
                    )
                )
                return int(mask.sum())

            for c in ("player_id", "player_name", "team"):
                if c not in df.columns:
                    df[c] = None

            snap_pct_vals = []
            for _, row in df.iterrows():
                pid = row.get("player_id")
                team = row.get("team") or row.get("recent_team")
                plays = team_plays.get(team, 0)
                pcount = player_play_count(pid, team)
                snap_pct_vals.append(float(pcount) / plays if plays not in [0, None] else 0)

            df["snap_pct"] = snap_pct_vals

            # If derived snap_pct all zero, fall back to usage heuristic
            if int((df["snap_pct"] > 0).sum()) == 0:
                pbp_df = None

        if pbp_df is None or pbp_df.empty:
            # Heuristic fallback: approximate snap_pct from attempts + carries + targets
            for fld in ("attempts", "carries", "targets"):
                if fld not in df.columns:
                    df[fld] = 0

            df["_raw_play_count"] = (
                df["attempts"].fillna(0)
                + df["carries"].fillna(0)
                + df["targets"].fillna(0)
            )

            if "team" in df.columns:
                team_totals = df.groupby("team")["_raw_play_count"].transform("sum")
                df["snap_pct"] = df.apply(
                    lambda r: float(r["_raw_play_count"]) / team_totals.loc[r.name]
                    if team_totals.loc[r.name] not in [0, None]
                    else 0,
                    axis=1,
                )
            else:
                total = df["_raw_play_count"].sum()
                df["snap_pct"] = df["_raw_play_count"].apply(lambda v: float(v) / total if total not in [0, None] else 0)

            df.drop(columns=[c for c in ("_raw_play_count",) if c in df.columns], inplace=True)

    # ------------------------------------------------------------
    # Keep only what we need
    # ------------------------------------------------------------
    keep = ["player_id", "player_name", "team", "position", "snap_pct"]
    existing = [c for c in keep if c in df.columns]
    df = df[existing].copy()

    return df
