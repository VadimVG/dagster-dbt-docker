import dagster as dg
from dagster_easy.utils.database.postgres import get_pg_connect
from dagster_easy.utils.helpers import DagsterAssetKind


@dg.asset(
    description="""
        RU: Проверка работоспособности аналитической базы данных.\n
            \n
        EN: Checking the functionality of the analytical database.
    """,
    kinds={
        DagsterAssetKind.PYTHON,
    },
    group_name="healthchecks",
)
def test_db_connection(context: dg.AssetExecutionContext) -> None:
    pg_conn = get_pg_connect()
    query = "SELECT version();"
    res = pg_conn.execute_query(query)
    context.log.info(res)


@dg.asset(
    description="""
        RU: Создание необходимых схем, если они не созданы.
            \n
        EN: Creating the necessary schemas if they do not exist.
    """,
    kinds={
        DagsterAssetKind.PYTHON,
    },
    group_name="healthchecks",
    deps = [test_db_connection]
)
def ready_schemas(context: dg.AssetExecutionContext) -> None:
    pg_conn = get_pg_connect()
    schemas = ["test", "raw_data"]
    query = ';\n'.join([f"create schema if not exists {schema}" for schema in schemas])
    context.log.info(f"Start command:\n{query}")
    pg_conn.execute_query(query)


verify_database_availability_job = dg.define_asset_job(
    name="verify_database_availability_job",
    description = """
                    RU: Job для проверки рабостоспособности аналитической базы данных.\n
                        \n
                    EN: Job to test the functionality of the analytical database.\n
                """,
    selection=[test_db_connection, ready_schemas],
)


            