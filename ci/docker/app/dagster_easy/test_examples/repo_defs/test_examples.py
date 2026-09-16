import dagster as dg
from dagster_celery import celery_executor

from dagster_easy.resources.resources import dbt_resource
from dagster_easy.test_examples.jobs import (
    asset_example,
    op_example,
    dynamic_output_op_example,
)


test_examples = dg.create_repository_using_definitions_args(
    name = "test_examples",

    assets=dg.load_assets_from_modules([
        asset_example,
        op_example,
        dynamic_output_op_example,
    ]),

    jobs=[
        asset_example.asset_example_job,
        op_example.op_example_job,
        dynamic_output_op_example.dynamic_output_op_example_job,
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