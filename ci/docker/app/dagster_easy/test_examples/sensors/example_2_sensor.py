import dagster as dg

from dagster_easy.test_examples.jobs.jobs import example_2_job




@dg.sensor(
    job=example_2_job,
    minimum_interval_seconds=15,
    default_status=dg.DefaultSensorStatus.STOPPED
)
def example_2_sensor(context: dg.RunStatusSensorContext):
    result = dg.SkipReason("Skipped run") 
    run_records = context.instance.get_run_records(
        dg.RunsFilter(
            job_name="example_2_job",
            statuses=[dg.DagsterRunStatus.STARTED, dg.DagsterRunStatus.QUEUED, dg.DagsterRunStatus.STARTING],
        )
    )
    if len(run_records) == 0:
        result = dg.RunRequest(
            run_key=None,
            job_name="example_2_job"
        )
    yield result