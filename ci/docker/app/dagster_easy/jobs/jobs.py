import dagster as dg

from dagster_easy.assets import verify_database_availability

assets = dg.load_assets_from_modules(modules = [
    verify_database_availability,
    ]
)

verify_database_availability_job = dg.define_asset_job(
    name="verify_database_availability_job",
    description = """
                    RU: Job для проверки рабостоспособности аналитической базы данных.\n
                        \n
                    EN: Job to test the functionality of the analytical database.\n
                """,
    selection="db_connection",
)


