"""
    RU: Пример создания базовых ассетов.
    EN: An example of creating basic assets.
"""


import dagster as dg
import pandas as pd

from dagster_dbt import (
    DbtCliResource
)

import time

from dagster_easy.project import (
    dbt_project
)

from dagster_easy.utils.dbt.executors import execute_dbt_and_cleanup
from dagster_easy.utils.helpers import DagsterAssetKind




@dg.asset(
    kinds={
        DagsterAssetKind.PYTHON,
    },
    group_name="group_1",
)
def api_data(context: dg.AssetExecutionContext) -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "a":[1, 2, 3],
            "b": [10, 20, 30]
        }
    )
    context.log.info(df)
    time.sleep(5)
    return df


@dg.asset(
    kinds={
        DagsterAssetKind.PYTHON,
    },
    group_name="group_1",
)
def modify_api_data(context: dg.AssetExecutionContext, api_data: pd.DataFrame) -> pd.DataFrame:
    df = api_data
    df["c"] = None
    for i in range(len(df)):
        df["c"][i] = i+1
    time.sleep(5)
    context.log.info(df)
    return df


@dg.asset(
    kinds={
        DagsterAssetKind.PYTHON,
    },
    deps=[modify_api_data],
    group_name="group_1",
)
def api_data_raw_table(context: dg.AssetExecutionContext) -> None:
    context.log.info("loading data to db...")
    time.sleep(5)
    context.log.info("success")


@dg.asset(
    kinds={
        DagsterAssetKind.PYTHON,
    },
    required_resource_keys={"dbt"},
    deps=[modify_api_data],
    group_name="group_1",
)
def api_data_copy(context: dg.AssetExecutionContext) -> None:
    context.log.info("copy data...")
    time.sleep(5)
    context.log.info("success")


@dg.asset(
    kinds={
        DagsterAssetKind.DBT,
    },
    deps=[api_data_raw_table, api_data_copy],
    group_name="group_1",
)
def some_dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    command = ["run", "-f", "-s", "test_model"]
    return execute_dbt_and_cleanup(context=context, dbt=dbt, command=command)


asset_example_job = dg.define_asset_job(
    name="asset_example_job",
    description = """
                    RU: Пример создания job из ассетов.\n
                        В данном случае импортируется весь модуль с ассетами через метод load_assets_from_modules.\n
                        Можно выгрузить ассеты по аналогии с операциями (то есть каждую функцию по отдельности),\n
                        но рекомендуется использовать именно load_assets_from_modules.\n\n
                        \n
                    EN: An example of creating a job from assets.\n
                        In this case, the entire module with assets is imported using the load_assets_from_modules method.\n
                        You can unload assets in a similar way to operations (i.e., each function individually),\n
                        but it is recommended to use load_assets_from_modules.\n
                """,
    selection=[api_data, modify_api_data, api_data_raw_table, api_data_copy, some_dbt_models],
)

