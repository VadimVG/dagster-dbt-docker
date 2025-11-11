import dagster as dg

from dagster_easy.utils.database.postgres import PostgreDatabaseConnector

@dg.asset(
    description="""
        RU: Проверка работоспособности аналитической базы данных.\n
            \n
        EN: Checking the functionality of the analytical database.
    """,
    kinds={
        "Python",
    },
    group_name="healthchecks",
)
def db_connection(context: dg.AssetExecutionContext) -> None:
    with PostgreDatabaseConnector() as db:
        data = db.execute_query("SELECT version();")
    context.log.info(data)



@dg.asset(
    description="""
        RU: Создание необходимых схем, если они не созданы.
            \n
        EN: Creating the necessary schemas if they do not exist.
    """,
    kinds={
        "Python",
    },
    group_name="healthchecks",
    deps = [db_connection]
)
def ready_schemas(context: dg.AssetExecutionContext) -> None:
    with PostgreDatabaseConnector() as db:

        shemas = ["test", "raw_data"]
        for schema in shemas:
            db.execute_command(
                f"create schema if not exists {schema}"
            )


            