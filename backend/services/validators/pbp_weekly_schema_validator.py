import polars as pl
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
LOCAL_PBP_DIR = BASE_DIR / "tmp" / "kramerbot_pbp_cache"


def load_weekly_from_pbp(season: int, week: int) -> pl.DataFrame:
    """
    Phase 2: Pure Polars weekly builder.
    Fast, schema-aware, and source-agnostic.
    """

    path = LOCAL_PBP_DIR / f"pbp_{season}.parquet"
    if not path.exists():
        print(f"⚠️ Missing PBP parquet for {season}")
        return pl.DataFrame()

    lf = pl.scan_parquet(path).filter(pl.col("week") == week)

    # RECEIVING
    rec = (
        lf.filter(pl.col("pass_attempt") == 1)
        .groupby(["receiver_id", "receiver", "posteam"])
        .agg([
            pl.count().alias("targets"),
            pl.sum("complete_pass").alias("receptions"),
            pl.sum("yards_gained").alias("receiving_yards"),
            pl.sum("touchdown").alias("receiving_tds"),
            pl.sum("air_yards").alias("receiving_air_yards"),
            pl.sum("first_down").alias("receiving_first_downs"),
            pl.sum("epa").alias("receiving_epa"),
        ])
        .rename({
            "receiver_id": "player_id",
            "receiver": "player_name",
            "posteam": "team",
        })
    )

    # RUSHING
    rush = (
        lf.filter(pl.col("rush_attempt") == 1)
        .groupby(["rusher_id", "rusher", "posteam"])
        .agg([
            pl.count().alias("carries"),
            pl.sum("yards_gained").alias("rushing_yards"),
            pl.sum("touchdown").alias("rushing_tds"),
            pl.sum("epa").alias("rushing_epa"),
        ])
        .rename({
            "rusher_id": "player_id",
            "rusher": "player_name",
            "posteam": "team",
        })
    )

    # PASSING
    pas = (
        lf.filter(pl.col("pass_attempt") == 1)
        .groupby(["passer_id", "passer", "posteam"])
        .agg([
            pl.sum("pass_attempt").alias("attempts"),
            pl.sum("complete_pass").alias("completions"),
            pl.sum("yards_gained").alias("passing_yards"),
            pl.sum("touchdown").alias("passing_tds"),
            pl.sum("interception").alias("interceptions"),
            pl.sum("air_yards").alias("passing_air_yards"),
            pl.sum("first_down").alias("passing_first_downs"),
            pl.sum("epa").alias("passing_epa"),
        ])
        .rename({
            "passer_id": "player_id",
            "passer": "player_name",
            "posteam": "team",
        })
    )

    # MERGE
    weekly = rec.join(rush, on=["player_id", "player_name", "team"], how="outer")
    weekly = weekly.join(pas, on=["player_id", "player_name", "team"], how="outer")

    # Add season/week
    weekly = weekly.with_columns([
        pl.lit(season).alias("season"),
        pl.lit(week).alias("week"),
    ])

    # Fill missing numeric columns
    weekly = weekly.fill_null(0)

    # Fantasy scoring
    weekly = weekly.with_columns([
        (
            (pl.col("rushing_yards") / 10) +
            (pl.col("receiving_yards") / 10) +
            (pl.col("rushing_tds") * 6) +
            (pl.col("receiving_tds") * 6) +
            (pl.col("passing_yards") / 25) +
            (pl.col("passing_tds") * 4) -
            (pl.col("interceptions") * 2)
        ).alias("fantasy_points"),

        (pl.col("fantasy_points") + pl.col("receptions")).alias("fantasy_points_ppr"),
        (pl.col("fantasy_points") + (pl.col("receptions") * 0.5)).alias("fantasy_points_0.5ppr"),
    ])

    return weekly.collect()
