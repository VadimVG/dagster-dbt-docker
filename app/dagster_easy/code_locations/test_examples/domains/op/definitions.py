import dagster as dg

from dagster_easy.shared.dbt.resources import dbt_resource
from dagster_easy.shared.helpers import get_executor
from dagster_easy.code_locations.test_examples.domains.op.dynamic_output_op_example import (
    job as dynamic_output_op_example,
)
from dagster_easy.code_locations.test_examples.domains.op.op_example import (
    job as op_example,
)


op = dg.create_repository_using_definitions_args(
    name="op",
    jobs=[
        op_example.op_example_job,
        dynamic_output_op_example.dynamic_output_op_example_job,
    ],
    schedules=[],
    sensors=[],
    resources={"dbt": dbt_resource},
    executor=get_executor(),
)
