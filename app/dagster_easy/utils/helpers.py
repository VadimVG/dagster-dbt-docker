import dagster as dg
import os
import pytz
from datetime import datetime
from enum import StrEnum


def get_current_moscow_datetime() -> datetime:
    return datetime.now(pytz.timezone('Europe/Moscow'))\
            .replace(microsecond=0, tzinfo=None)


class DagsterAssetKind(StrEnum):
    "Constants for kinds in assets"
    PYTHON = "python"
    DBT = "dbt"
    PANDAS = "pandas"
    MSSQL = "mssql"
    SSAS = "ssas"


class DagsterAssetRefreshConfig(dg.Config):
    "Configuration of update types for assets"
    
    class RefreshType(StrEnum):
        INC = "inc"
        DEEP_INC = "deep_inc" 
        FULL = "full"

    type: RefreshType


class DagsterBuildType(StrEnum):
    "Values of the DAGSTER_BUILD_TYPE env var: how the project is deployed"
    DOCKER = "docker"
    K8S = "k8s"


def get_executor() -> dg.ExecutorDefinition:
    """Executor for the current deployment.

    docker: Celery executor, steps run on the Celery workers.
    k8s: multiprocess executor, steps run inside the run pod created by K8sRunLauncher.
    """
    build_type = os.getenv("DAGSTER_BUILD_TYPE", DagsterBuildType.K8S)

    if build_type == DagsterBuildType.DOCKER:
        from dagster_celery import celery_executor
        return celery_executor

    if build_type == DagsterBuildType.K8S:
        return dg.multiprocess_executor.configured({"max_concurrent": 4})

    raise ValueError(
        f"Unknown DAGSTER_BUILD_TYPE={build_type!r}, "
        f"expected one of: {', '.join(DagsterBuildType)}"
    )