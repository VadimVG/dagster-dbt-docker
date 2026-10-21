import os
import shutil

import boto3
import dagster as dg

from dagster_easy.shared.helpers import DagsterAssetKind


BUCKET = "ai-video"


@dg.asset(
    description="Checking the S3 access and the image of the run pod: lists the bucket ai-video.",
    kinds={
        DagsterAssetKind.PYTHON,
    },
    group_name="healthchecks",
)
def s3_check(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
    # ffmpeg exists only in the ai-video image, so this shows which image the run pod uses
    context.log.info(f"ffmpeg: {shutil.which('ffmpeg')}")
    context.log.info(f"S3 endpoint: {os.getenv('AWS_ENDPOINT_URL_S3')}")

    # Keys and endpoint come from the env (s3-credentials, AWS_ENDPOINT_URL_S3)
    response = boto3.client("s3").list_objects_v2(Bucket=BUCKET)
    keys = [obj["Key"] for obj in response.get("Contents", [])]
    context.log.info(f"Objects in s3://{BUCKET}: {keys}")

    return dg.MaterializeResult(metadata={"objects": len(keys)})


s3_check_job = dg.define_asset_job(
    name="s3_check_job",
    description="Job to test the S3 access of the ai-video code location.",
    selection=[s3_check],
)
