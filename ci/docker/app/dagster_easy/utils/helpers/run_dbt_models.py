import dagster as dg

from dagster_dbt import (
    DbtCliInvocation
)

import shutil

from dagster_easy.project import (
    dbt_project
)




def custom_dbt_model_executor_1(
    context: dg.OpExecutionContext,
    dbt_cli: DbtCliInvocation,
):
    for raw_event in dbt_cli.stream_raw_events():
        context.log.info(raw_event) # вывод логов dbt из cli
    
    context.log.info(f"Folder for current run `{dbt_cli.target_path}`")
    shutil.rmtree(dbt_cli.target_path) # dagster создает для каждого запуска dbt отдельную директорию, удаляем их после выполнения обновлений dbt моделей
    context.log.info(f"Folder `{dbt_cli.target_path}` was deleted successfully")


def custom_dbt_model_executor_2(
    context: dg.OpExecutionContext,
    dbt_cli: DbtCliInvocation,
):
    manifest_path = dbt_project.manifest_path
    for raw_event in dbt_cli.stream_raw_events():
        context.log.info(raw_event) # вывод логов dbt из cli
        yield from raw_event.to_default_asset_events(manifest=manifest_path)
    context.log.info(f"Folder for current run `{dbt_cli.target_path}`")
    shutil.rmtree(dbt_cli.target_path) # dagster создает для каждого запуска dbt отдельную директорию, удаляем их после выполнения обновлений dbt моделей
    context.log.info(f"Folder `{dbt_cli.target_path}` was deleted successfully")


def clear_tmp_dagster_dbt_dir(
    context: dg.OpExecutionContext,
    dbt_cli: DbtCliInvocation
) -> None:
    context.log.info(f"Folder for current run `{dbt_cli.target_path}`")
    shutil.rmtree(dbt_cli.target_path) # dagster создает для каждого запуска dbt отдельную директорию, удаляем их после выполнения обновлений dbt моделей
    context.log.info(f"Folder `{dbt_cli.target_path}` was deleted successfully")
