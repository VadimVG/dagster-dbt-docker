import dagster as dg

from dagster_easy.shared.helpers import get_executor
from dagster_easy.code_locations.main.domains.healthcheck.verify_database_availability import (
    job as verify_database_availability,
)


healthcheck = dg.create_repository_using_definitions_args(
    name="healthcheck",
    assets=dg.load_assets_from_modules([verify_database_availability]),
    jobs=[verify_database_availability.verify_database_availability],
    schedules=[],
    sensors=[],
    executor=get_executor(),
)
