import pandas as pd

def load_pbp(season: int) -> pd.DataFrame:
    """
    Loads PBP parquet directly from nflverse GitHub.
    """
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        f"pbp/pbp_{season}.parquet"
    )

    print(f"📡 Downloading PBP from {url}")
    return pd.read_parquet(url)


def load_weekly_from_pbp(season: int, week: int) -> pd.DataFrame:
    """
    Builds weekly player-level stats from PBP.
    """
    pbp = load_pbp(season)

    pbp_week = pbp[pbp["week"] == week].copy()
    if pbp_week.empty:
        return pd.DataFrame()

    # -----------------------------
    # RECEIVING
    # -----------------------------
    rec_events = pbp_week[pbp_week["pass_attempt"] == 1]
    rec_group = rec_events.groupby(
        ["receiver_id", "receiver", "posteam"], dropna=True
    )

    rec_df = rec_group.agg(
        targets=("receiver_id", "count"),
        receptions=("complete_pass", "sum"),
        receiving_yards=("yards_gained", "sum"),
        receiving_tds=("touchdown", "sum"),
        air_yards=("air_yards", "sum"),
        receiving_first_downs=("first_down", "sum"),
        receiving_epa=("epa", "sum"),
    ).reset_index()

    rec_df.rename(
        columns={
            "receiver_id": "player_id",
            "receiver": "player_name",
            "posteam": "team",
        },
        inplace=True,
    )

    # -----------------------------
    # RUSHING
    # -----------------------------
    rush_events = pbp_week[pbp_week["rush_attempt"] == 1]
    rush_group = rush_events.groupby(
        ["rusher_id", "rusher", "posteam"], dropna=True
    )

    rush_df = rush_group.agg(
        carries=("rusher_id", "count"),
        rushing_yards=("yards_gained", "sum"),
        rushing_tds=("touchdown", "sum"),
        rushing_epa=("epa", "sum"),
    ).reset_index()

    rush_df.rename(
        columns={
            "rusher_id": "player_id",
            "rusher": "player_name",
            "posteam": "team",
        },
        inplace=True,
    )

    # -----------------------------
    # PASSING
    # -----------------------------
    pass_events = pbp_week[pbp_week["pass_attempt"] == 1]
    pass_group = pass_events.groupby(
        ["passer_id", "passer", "posteam"], dropna=True
    )

    pass_df = pass_group.agg(
        attempts=("pass_attempt", "sum"),
        completions=("complete_pass", "sum"),
        passing_yards=("yards_gained", "sum"),
        passing_tds=("touchdown", "sum"),
        interceptions=("interception", "sum"),
        passing_epa=("epa", "sum"),
    ).reset_index()

    pass_df.rename(
        columns={
            "passer_id": "player_id",
            "passer": "player_name",
            "posteam": "team",
        },
        inplace=True,
    )

    # -----------------------------
    # MERGE ALL THREE
    # -----------------------------
    from functools import reduce
    dfs = [rec_df, rush_df, pass_df]

    weekly = reduce(
        lambda left, right: pd.merge(
            left, right, on=["player_id", "player_name", "team"], how="outer"
        ),
        dfs,
    )

    weekly["season"] = season
    weekly["week"] = week

    # -----------------------------
    # FANTASY
    # -----------------------------
    for col in [
        "targets", "receptions", "receiving_yards", "receiving_tds",
        "carries", "rushing_yards", "rushing_tds",
        "attempts", "passing_yards", "passing_tds", "interceptions"
    ]:
        if col not in weekly.columns:
            weekly[col] = 0

    weekly["fantasy_points"] = (
        weekly["rushing_yards"] / 10
        + weekly["receiving_yards"] / 10
        + weekly["rushing_tds"] * 6
        + weekly["receiving_tds"] * 6
        + weekly["passing_yards"] / 25
        + weekly["passing_tds"] * 4
        - weekly["interceptions"] * 2
    )

    weekly["fantasy_points_ppr"] = weekly["fantasy_points"] + weekly["receptions"]
    weekly["fantasy_points_0.5ppr"] = weekly["fantasy_points"] + weekly["receptions"] * 0.5

    return weekly
