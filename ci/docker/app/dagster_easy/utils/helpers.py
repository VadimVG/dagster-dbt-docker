import dagster as dg
import pytz
from datetime import datetime
from enum import StrEnum


def get_current_moscow_datetime() -> datetime:
    return datetime.now(pytz.timezone('Europe/Moscow'))\
            .replace(microsecond=0, tzinfo=None)


class DagsterAssetKind(StrEnum):
    """
        RU: Константы для обозначений kinds в ассетах\n
            \n
        EN: Constants for kinds in assets\n
    """
    PYTHON = "python"
    DBT = "dbt"
    PANDAS = "pandas"
    MSSQL = "mssql"
    SSAS = "ssas"


class DagsterAssetRefreshConfig(dg.Config):
    """
        RU: Конфигурация типов обновления для ассетов\n
            \n
        EN: Configuration of update types for assets\n
    """
    
    class RefreshType(StrEnum):
        INC = "inc"
        DEEP_INC = "deep_inc" 
        FULL = "full"
    
    type: RefreshType