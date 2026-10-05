import dagster as dg
from dagster_celery import celery_executor

from dagster_easy.resources.resources import dbt_resource
from dagster_easy.jobs import (
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
    
    executor=celery_executor,
    
)