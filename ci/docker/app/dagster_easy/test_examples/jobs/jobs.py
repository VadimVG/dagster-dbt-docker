import dagster as dg

from dagster_easy.test_examples.assets import example_1

from dagster_easy.test_examples.ops.example_2 import (
    get_important_data,
    create_df,
    load_df_to_db,
    refresh_dbt_models,
)

from dagster_easy.test_examples.ops.example_3 import (
    generate_dynamic_outputs,
    process_dynamic_output,
)



example_1_assets = dg.load_assets_from_modules(modules = [
    example_1,
    ]
)

example_1_job = dg.define_asset_job(
    name="example_1_job",
    description = """
                    Пример создания джоба из ассетов.\n
                    В данном случае импортируется весь модуль с ассетами через метод load_assets_from_modules.\n
                    Можно выгрузить ассеты по аналогии с операциями (то есть каждую функцию по отдельности), но рекомендуется использовать именно load_assets_from_modules.\n
                    Все зависимости ассетов указываются при их создании в аргументе deps.
                """,
    selection=example_1_assets,
)



@dg.job(
    description = """
                    Пример создания джоба из базовых операций.\n
                    Все зависимости операций указываются при создании джоба.
                """
)
def example_2_job():
    res = get_important_data()
    df = create_df(json = res)
    load_df_to_db(df=df)
    refresh_dbt_models(start_after=df)


@dg.job(
    description= """
                    Пример создания джоба из динамических операций.\n
                    Все зависимости операций указываются при создании джоба, по аналогии с джобом из базовых операций.\n
                    Данный джоб создает динамическую операцию для каждого значения, полученного из generate_dynamic_outputs.
                """
)
def example_3_job():
    dynamic_outputs = generate_dynamic_outputs()
    dynamic_outputs.map(process_dynamic_output)