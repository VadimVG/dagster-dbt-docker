"""
    Пример создания базовых ассетов
    
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

from dagster_easy.utils.helpers.run_dbt_models import (
    custom_dbt_model_executor_1,
)




@dg.asset(
    kinds={
        "Python",
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
        "Python"
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
        "Python",
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
        "Python",
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
        "dbt",
    },
    deps=[api_data_raw_table, api_data_copy],
    group_name="group_1",
)
def some_dbt_models(context: dg.AssetExecutionContext, dbt: DbtCliResource):
    dbt_cli = dbt.cli(["run"], manifest=dbt_project.manifest_path)
    return custom_dbt_model_executor_1(context=context, dbt_cli=dbt_cli)




