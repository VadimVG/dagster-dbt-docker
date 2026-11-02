import logging

import polars as pl

logger = logging.getLogger(__name__)


def clean_hourly_observations(rows: list[dict]) -> pl.DataFrame:
    df = (
        pl.DataFrame(rows, infer_schema_length=None)
        .with_columns(pl.col("time").str.to_datetime("%Y-%m-%dT%H:%M"))
        .drop_nulls(subset=["city", "time"])
        .unique(subset=["city", "time"], keep="last")
        .sort(["city", "time"])
    )
    logger.info("Dropped %s of %s rows", len(rows) - df.height, len(rows))
    return df
