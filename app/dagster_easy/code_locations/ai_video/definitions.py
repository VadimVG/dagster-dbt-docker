import dagster as dg

from dagster_easy.shared.helpers import get_executor
from dagster_easy.code_locations.ai_video.jobs import (
    s3_check,
)


import warnings
warnings.filterwarnings("ignore", category=dg.ExperimentalWarning)

defs = dg.Definitions(
    assets=dg.load_assets_from_modules([
        s3_check,
    ]),

    jobs=[
        s3_check.s3_check_job,
    ],

    schedules=[
    ],

    sensors=[
    ],

    executor=get_executor(),
)
