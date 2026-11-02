import dagster as dg
import polars as pl

from dagster_easy.shared.dlt.loader import load_to_raw
from dagster_easy.shared.helpers import DagsterAssetKind, DagsterAssetRefreshConfig
from dagster_easy.shared.quality.gx import validate_dataframe
from dagster_easy.code_locations.main.domains.weather.api_open_meteo_hourly_observations.expectations import (
    hourly_observations_suite,
)
from dagster_easy.code_locations.main.domains.weather.api_open_meteo_hourly_observations.source import (
    hourly_observations,
)
from dagster_easy.code_locations.main.domains.weather.api_open_meteo_hourly_observations.transforms import (
    clean_hourly_observations,
)

PAST_DAYS = {
    DagsterAssetRefreshConfig.RefreshType.INC: 2,
    DagsterAssetRefreshConfig.RefreshType.DEEP_INC: 14,
}


@dg.asset(kinds={DagsterAssetKind.DLT}, group_name="weather")
def extracted_api_open_meteo_hourly_observations(
    context: dg.AssetExecutionContext,
    config: DagsterAssetRefreshConfig,
) -> list[dict]:
    rows = list(hourly_observations(past_days=PAST_DAYS[config.type]))
    context.add_output_metadata({"rows": len(rows)})
    return rows


@dg.asset(kinds={DagsterAssetKind.POLARS}, group_name="weather")
def cleaned_api_open_meteo_hourly_observations(
    context: dg.AssetExecutionContext,
    extracted_api_open_meteo_hourly_observations: list[dict],
) -> pl.DataFrame:
    df = clean_hourly_observations(extracted_api_open_meteo_hourly_observations)
    context.add_output_metadata({"rows": df.height})
    return df


@dg.asset_check(asset=cleaned_api_open_meteo_hourly_observations, blocking=True)
def validate_cleaned_api_open_meteo_hourly_observations(
    cleaned_api_open_meteo_hourly_observations: pl.DataFrame,
) -> dg.AssetCheckResult:
    result = validate_dataframe(cleaned_api_open_meteo_hourly_observations, hourly_observations_suite())
    failed = [r.expectation_config.type for r in result.results if not r.success]
    return dg.AssetCheckResult(passed=result.success, metadata={"failed_expectations": failed})


@dg.asset(kinds={DagsterAssetKind.DLT}, group_name="weather")
def raw_api_open_meteo_hourly_observations(
    context: dg.AssetExecutionContext,
    cleaned_api_open_meteo_hourly_observations: pl.DataFrame,
) -> dg.MaterializeResult:
    load_info = load_to_raw(
        cleaned_api_open_meteo_hourly_observations,
        table_name="api_open_meteo_hourly_observations",
        primary_key=["city", "time"],
    )
    context.log.info(str(load_info))
    return dg.MaterializeResult(metadata={"rows": cleaned_api_open_meteo_hourly_observations.height})


api_open_meteo_hourly_observations = dg.define_asset_job(
    name="api_open_meteo_hourly_observations",
    description="Open-Meteo: extract with dlt, clean with Polars, validate with GX, load to raw.",
    selection=[
        extracted_api_open_meteo_hourly_observations,
        cleaned_api_open_meteo_hourly_observations,
        raw_api_open_meteo_hourly_observations,
    ],
)


api_open_meteo_hourly_observations_inc_schedule = dg.ScheduleDefinition(
    name="api_open_meteo_hourly_observations_inc_schedule",
    job=api_open_meteo_hourly_observations,
    cron_schedule="0 * * * *",
    execution_timezone="Europe/Moscow",
)

api_open_meteo_hourly_observations_deep_inc_schedule = dg.ScheduleDefinition(
    name="api_open_meteo_hourly_observations_deep_inc_schedule",
    job=api_open_meteo_hourly_observations,
    cron_schedule="30 3 * * *",
    execution_timezone="Europe/Moscow",
    run_config=dg.RunConfig(
        ops={
            "extracted_api_open_meteo_hourly_observations": DagsterAssetRefreshConfig(
                type=DagsterAssetRefreshConfig.RefreshType.DEEP_INC,
            ),
        }
    ),
)
