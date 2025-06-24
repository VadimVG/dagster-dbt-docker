import dagster as dg

from dagster_easy.utils.database.postgres import PostgreDatabaseConnector

@dg.asset(
    kinds={
        "Python",
    },
    group_name="healthchecks",
)
def db_connection(context: dg.AssetExecutionContext) -> None:
    with PostgreDatabaseConnector() as db:
        data = db.execute_query("SELECT version();")
    context.log.info(data)