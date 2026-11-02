import os
from urllib.parse import quote_plus

import dlt
import polars as pl


def load_to_raw(df: pl.DataFrame, table_name: str, primary_key: list[str]):
    credentials = (
        f"postgresql://{quote_plus(os.environ['DWH_USER'])}:{quote_plus(os.environ['DWH_PASSWORD'])}"
        f"@{os.environ['DWH_HOST']}:{os.environ['DWH_PORT']}/{os.environ['DWH_DB']}"
    )
    pipeline = dlt.pipeline(
        pipeline_name=table_name,
        destination=dlt.destinations.postgres(
            credentials=credentials,
            staging_dataset_name_layout="dlt_staging",
        ),
        dataset_name="raw",
    )
    return pipeline.run(
        df.to_arrow(),
        table_name=table_name,
        write_disposition="merge",
        primary_key=primary_key,
    )
