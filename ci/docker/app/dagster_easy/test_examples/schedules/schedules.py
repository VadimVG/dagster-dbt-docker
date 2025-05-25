import dagster as dg

from dagster_easy.test_examples.jobs.jobs import (
    example_1_job,
    example_3_job,
)




example_1_schedule = dg.ScheduleDefinition(
    job=example_1_job,
    cron_schedule="30 0 * * *",
)

example_3_schedule = dg.ScheduleDefinition(
    job=example_3_job,
    cron_schedule="30 0 * * *",
)



