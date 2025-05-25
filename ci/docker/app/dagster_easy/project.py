from dagster_dbt import DbtProject

import os

from pathlib import Path




dbt_project = DbtProject(
    project_dir=Path(__file__).joinpath("..", "..", "dbt", "projects").resolve(),
    target="prod",
    
)
# dbt_project.prepare_if_dev()

