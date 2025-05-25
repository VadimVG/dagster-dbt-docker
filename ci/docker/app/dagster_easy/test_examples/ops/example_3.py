"""
    Пример создания динамических операций.
"""



import dagster as dg




tables_to_load = [
    "aaa",
    "bbb",
    "ccc"
]


@dg.op(
    config_schema={
        "tables_to_load": dg.Field([str], tables_to_load)
    },
    out=dg.DynamicOut())
def generate_dynamic_outputs(context: dg.OpExecutionContext):
    for i in context.op_config["tables_to_load"]:
        yield dg.DynamicOutput(value=i, mapping_key=f"key_{i}")


@dg.op
def process_dynamic_output(context: dg.OpExecutionContext, value: str):
    context.log.info(value)
    return value   

