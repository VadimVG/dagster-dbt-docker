import dagster as dg

from dagster_easy.shared.dbt.resources import dbt_resource
from dagster_easy.shared.helpers import get_executor
from dagster_easy.code_locations.test_examples.jobs import (
    asset_example,
    op_example,
    dynamic_output_op_example,
)


import warnings
warnings.filterwarnings("ignore", category=dg.ExperimentalWarning)

defs = dg.Definitions(
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

    executor=get_executor(),
)
