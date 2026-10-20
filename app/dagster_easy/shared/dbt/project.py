from dagster_dbt import DbtProject

from pathlib import Path


dbt_project = DbtProject(
    # parents: dbt -> shared -> dagster_easy -> app
    project_dir=Path(__file__).resolve().parents[3].joinpath("dbt", "projects"),
    target="prod",
    
)

