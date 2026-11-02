import great_expectations as gx
import polars as pl


def validate_dataframe(df: pl.DataFrame, suite: gx.ExpectationSuite):
    context = gx.get_context(mode="ephemeral")
    batch_definition = (
        context.data_sources.add_pandas("polars_frame")
        .add_dataframe_asset("frame")
        .add_batch_definition_whole_dataframe("whole_frame")
    )
    batch = batch_definition.get_batch(batch_parameters={"dataframe": df.to_pandas()})
    return batch.validate(suite)
