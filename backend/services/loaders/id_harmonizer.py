import pandas as pd

# ------------------------------------------------------------
# Load the universal nflverse player ID crosswalk
# ------------------------------------------------------------
def load_player_id_map() -> pd.DataFrame:
    """
    Loads the official nflverse player ID crosswalk.
    Contains:
      - player_id (GSIS)
      - gsis_id
      - pfr_id
      - sportradar_id
      - espn_id
      - fantasy_id
      - nflverse_id (canonical)
    """
    url = (
        "https://github.com/nflverse/nflverse-data/releases/download/"
        "players/players.parquet"
    )

    print("📡 Loading universal player ID map (players.parquet)")
    df = pd.read_parquet(url)

    # Normalize column names
    df = df.rename(columns={"player_id": "gsis_id"})  # nflverse uses player_id = gsis_id

    return df


# ------------------------------------------------------------
# Harmonize IDs between any dataset and the roster
# ------------------------------------------------------------
def harmonize_ids(df: pd.DataFrame, roster: pd.DataFrame) -> pd.DataFrame:
    """
    Harmonizes IDs between weekly data and roster using the nflverse player ID map.
    Returns df with a guaranteed join key: nflverse_id.
    """

    players = load_player_id_map()

    # --------------------------------------------------------
    # Step 1: Try to find a shared ID column between df + players
    # --------------------------------------------------------
    possible_keys = ["gsis_id", "pfr_id", "sportradar_id", "espn_id", "fantasy_id"]

    join_key = None
    for key in possible_keys:
        if key in df.columns and key in players.columns:
            join_key = key
            break

    if join_key is None:
        print("⚠️ No shared ID between weekly data and player map — returning df unchanged")
        return df

    print(f"🔗 Harmonizing weekly data using player map on {join_key}")

    # --------------------------------------------------------
    # Step 2: Merge df → players to get nflverse_id
    # --------------------------------------------------------
    df = df.merge(
        players[["nflverse_id", join_key]],
        on=join_key,
        how="left"
    )

    # --------------------------------------------------------
    # Step 3: Merge roster → players to get nflverse_id
    # --------------------------------------------------------
    roster_join_key = None
    for key in possible_keys:
        if key in roster.columns and key in players.columns:
            roster_join_key = key
            break

    if roster_join_key is None:
        print("⚠️ No shared ID between roster and player map — returning df without roster merge")
        return df

    print(f"🔗 Harmonizing roster using player map on {roster_join_key}")

    roster = roster.merge(
        players[["nflverse_id", roster_join_key]],
        on=roster_join_key,
        how="left"
    )

    # --------------------------------------------------------
    # Step 4: Merge df + roster on nflverse_id
    # --------------------------------------------------------
    print("🔗 Final merge: weekly + roster on nflverse_id")

    roster_cols = ["nflverse_id"] + [c for c in ["team", "position"] if c in roster.columns]

    df = df.merge(
        roster[roster_cols],
        on="nflverse_id",
        how="left"
    )
    
    # --------------------------------------------------------
    # Step 5: Normalize positions (fix WR/TE issues)
    # --------------------------------------------------------
    if "position" in df.columns:
        df["position"] = (
            df["position"]
            .astype(str)
            .str.upper()
            .str.strip()
        )

        # Fix common hybrid / mislabeled positions
        df["position"] = df["position"].replace({
            "HB": "RB",
            "FB": "RB",
            "TE/HB": "TE",
            "WR/RB": "WR",
            "TE/FB": "TE",
            "": None,
            "NONE": None,
        })

        # Optional: treat hybrid strings as WR/TE eligible
        df.loc[df["position"].str.contains("WR", na=False), "position"] = "WR"
        df.loc[df["position"].str.contains("TE", na=False), "position"] = "TE"

    return df
