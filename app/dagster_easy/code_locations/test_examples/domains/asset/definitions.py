import dagster as dg

from dagster_easy.shared.dbt.resources import dbt_resource
from dagster_easy.shared.helpers import get_executor
from dagster_easy.code_locations.test_examples.domains.asset.asset_example import (
    job as asset_example,
)


asset = dg.create_repository_using_definitions_args(
    name="asset",
    assets=dg.load_assets_from_modules([asset_example]),
    jobs=[asset_example.asset_example],
    schedules=[],
    sensors=[],
    resources={"dbt": dbt_resource},
    executor=get_executor(),
)
