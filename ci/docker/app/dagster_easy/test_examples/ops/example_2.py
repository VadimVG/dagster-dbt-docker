"""
    Пример создания базовых операций.
"""


import dagster as dg
import pandas as pd

from dagster_dbt import (
    DbtCliResource
)

import time

from dagster_easy.utils.helpers.run_dbt_models import (
    custom_dbt_model_executor_1,
)




@dg.op
def get_important_data(context: dg.OpExecutionContext) -> dict:
    response = {
        "a": [1, 2],
        "b": [3, 4]
    }
    context.log.info(response)
    time.sleep(5)
    return response


@dg.op
def create_df(context: dg.OpExecutionContext, json: dict) -> pd.DataFrame:
    df = pd.DataFrame(json)
    context.log.info(df)
    time.sleep(1)
    return df


@dg.op
def load_df_to_db(context: dg.OpExecutionContext, df: pd.DataFrame) -> None:
    context.log.info("load dataframe to db")
    context.log.info(df)
    time.sleep(1)


@dg.op(
    out=dg.Out(dg.Nothing),
)
def refresh_dbt_models(context: dg.OpExecutionContext, dbt: DbtCliResource, start_after = ""):
    command = ["run", "-f", "-s", "tag:stages"]
    dbt_cli = dbt.cli(command)
    return custom_dbt_model_executor_1(context=context, dbt_cli=dbt_cli)

    



