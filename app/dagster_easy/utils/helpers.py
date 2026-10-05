import dagster as dg
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