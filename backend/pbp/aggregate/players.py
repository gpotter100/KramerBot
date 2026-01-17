import polars as pl

def aggregate_qb_efficiency(lf: pl.LazyFrame) -> pl.DataFrame:
    return (
        lf
        .filter(pl.col("qb_id").is_not_null())
        .groupby("qb_id")
        .agg([
            pl.count().alias("dropbacks"),
            pl.col("epa").sum().alias("total_epa"),
            pl.col("epa").mean().alias("epa_per_play"),
            pl.col("success").mean().alias("success_rate"),
            pl.col("pass_air_yards").mean().alias("avg_air_yards"),
        ])
        .sort("epa_per_play", descending=True)
        .collect()
    )
