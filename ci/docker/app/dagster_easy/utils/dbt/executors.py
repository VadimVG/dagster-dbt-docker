import dagster as dg
from dagster_dbt import DbtCliResource
import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
from dagster_easy.project import (
    dbt_project
)



def __delete_target_dir(context: dg.AssetExecutionContext, target_path: Path) -> None:
    pattern = lambda x: f"Folder for current run was {x} successfully:\n{target_path}"
    context.log.debug(pattern("created"))
    shutil.rmtree(target_path)
    context.log.debug(pattern("deleted"))


def execute_dbt_and_cleanup(
    context: dg.OpExecutionContext,
    dbt: DbtCliResource,
    command: Optional[List[str]],
    vars: Optional[Dict] = None,
    args: Optional[Dict] = None,
) -> None:
    if not command:
        context.log.info("Empty command")
        return
    if vars:
        command += ["--vars", json.dumps(vars)]
    if args:
        command += ["--args", json.dumps(args)]
    dbt_cli = dbt.cli(command, manifest=dbt_project.manifest_path)
    for raw_event in dbt_cli.stream_raw_events():
        context.log.info(raw_event)
    target_path = dbt_cli.target_path
    __delete_target_dir(context=context, target_path=target_path)




def execute_dbt_and_handle_error(
    context: dg.OpExecutionContext,
    dbt: DbtCliResource,
    command: List[str],
    vars: Optional[Dict] = None,
    args: Optional[Dict] = None,
) -> Dict:
    if vars:
        command += ["--vars", json.dumps(vars)]
    if args:
        command += ["--args", json.dumps(args)]
    try:
        dbt_cli = dbt.cli(command, manifest=dbt_project.manifest_path)
        for raw_event in dbt_cli.stream_raw_events():
            context.log.info(raw_event)
    except Exception as e:
        context.log.error(str(e))
    target_path = dbt_cli.target_path
    results_path = Path(target_path) / "run_results.json"
    with open(results_path, "r", encoding='windows-1251') as f:
        run_results = json.load(f).get("results")
    error_dict = defaultdict(list)
    for i in run_results:
        status = i.get("status", "")
        if status in ("skipped", "error"):
            model_name = i.get("relation_name").split('.')[-1].replace('"', "")
            error_dict[status].append(model_name)
    context.log.info("Dbt models to re-launch:")
    for k, v in error_dict.items():
        for i in v:
            context.log.info(f"status: {k}, name: {i}")
        context.log.info(f"{k}: {len(v)} models")
    models = sum(error_dict.values(), [])
    command = ["run", "f", "-s", *models]
    context.log.info(command)
    output_dict = {"command": command, "vars": vars, "args": args}
    return output_dict if len(models) > 0 else dict.fromkeys(output_dict.keys(), None)
















