import great_expectations as gx
import great_expectations.expectations as gxe


def hourly_observations_suite() -> gx.ExpectationSuite:
    return gx.ExpectationSuite(
        name="api_open_meteo_hourly_observations",
        expectations=[
            gxe.ExpectColumnValuesToNotBeNull(column="city"),
            gxe.ExpectColumnValuesToNotBeNull(column="time"),
            gxe.ExpectCompoundColumnsToBeUnique(column_list=["city", "time"]),
            gxe.ExpectColumnValuesToBeBetween(column="temperature_2m", min_value=-70, max_value=60),
            gxe.ExpectColumnValuesToBeBetween(column="relative_humidity_2m", min_value=0, max_value=100),
        ],
    )
