from dagster_dbt import DbtProject

from pathlib import Path


dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "dbt", "projects").resolve(),
    target="prod",
    
)

