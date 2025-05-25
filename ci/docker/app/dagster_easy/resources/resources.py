from dagster_dbt import DbtCliResource

from dagster_easy.project import dbt_project


dbt_resource = DbtCliResource(
    project_dir=dbt_project,
    # profiles_dir="app/dbt/projects",
    global_config_flags=["--no-use-colors", "--log-format", "json"],
)