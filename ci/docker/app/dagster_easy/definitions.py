import dagster as dg

from dagster_celery import celery_executor

from dagster_easy.resources.resources import(
    dbt_resource,
)

from dagster_easy.test_examples.assets import example_1

from dagster_easy.test_examples.jobs.jobs import (
    example_1_job,
    example_2_job,
)

from dagster_easy.test_examples.schedules.schedules import (
    example_1_schedule,
    example_3_schedule,
)

from dagster_easy.test_examples.sensors.example_2_sensor import example_2_sensor


import warnings
warnings.filterwarnings("ignore", category=dg.ExperimentalWarning)


all_assets = dg.load_assets_from_modules(modules = [
    example_1,
    ]
)

test_examples = dg.create_repository_using_definitions_args(
    name = "test_examples",

    assets=all_assets,

    jobs=[
        example_1_job,
        example_2_job,
    ],

    schedules=[
        example_1_schedule,
        example_3_schedule,
    ],

    sensors=[
        example_2_sensor,
    ],

    resources={
        "dbt": dbt_resource,
    },
    
    executor=celery_executor,
    
)


repo_1 = dg.create_repository_using_definitions_args(
    name="repo_1",

    assets=[
    ],

    jobs=[
    ],

    schedules=[
    ],

    sensors=[
    ],

    resources={
        "dbt": dbt_resource,
    },
    
    executor=celery_executor
)




