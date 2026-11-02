import dagster as dg

from dagster_easy.shared.helpers import get_executor
from dagster_easy.code_locations.main.domains.weather.api_open_meteo_hourly_observations import (
    job as api_open_meteo_hourly_observations,
)


weather = dg.create_repository_using_definitions_args(
    name="weather",
    assets=dg.load_assets_from_modules([api_open_meteo_hourly_observations]),
    asset_checks=[api_open_meteo_hourly_observations.validate_cleaned_api_open_meteo_hourly_observations],
    jobs=[api_open_meteo_hourly_observations.api_open_meteo_hourly_observations],
    schedules=[
        api_open_meteo_hourly_observations.api_open_meteo_hourly_observations_inc_schedule,
        api_open_meteo_hourly_observations.api_open_meteo_hourly_observations_deep_inc_schedule,
    ],
    sensors=[],
    executor=get_executor(),
)
