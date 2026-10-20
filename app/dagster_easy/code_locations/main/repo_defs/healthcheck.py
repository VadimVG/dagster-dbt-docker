import dagster as dg

from dagster_easy.shared.dbt.resources import dbt_resource
from dagster_easy.shared.helpers import get_executor
from dagster_easy.code_locations.main.jobs import (
    verify_database_availability,
)


healthcheck = dg.create_repository_using_definitions_args(
    name = "healthcheck",

    assets=dg.load_assets_from_modules([
        verify_database_availability,
    ]),

    jobs=[
        verify_database_availability.verify_database_availability_job,
    ],

    schedules=[
    ],

    sensors=[
    ],

    resources={
        "dbt": dbt_resource,
    },
    
    executor=get_executor(),
    
)