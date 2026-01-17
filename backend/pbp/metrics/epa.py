import polars as pl

def add_success(lf: pl.LazyFrame) -> pl.LazyFrame:
    return lf.with_columns(
        (pl.col("epa") > 0).cast(pl.Int64).alias("success")
    )
