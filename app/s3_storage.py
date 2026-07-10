import json
import os
from datetime import datetime, timezone


def build_eval_result_key(timestamp=None):
    run_timestamp = timestamp or datetime.now(timezone.utc)
    formatted_timestamp = run_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    return f"runs/eval_{formatted_timestamp}.json"


def upload_result_to_s3(payload, bucket_name=None, key=None, s3_client=None):
    if not payload:
        return {"uploaded": False, "reason": "empty_payload"}

    bucket = os.getenv("S3_EVAL_BUCKET") if bucket_name is None else bucket_name
    if not bucket:
        return {"uploaded": False, "reason": "missing_bucket"}

    object_key = key or build_eval_result_key()
    if s3_client is None:
        try:
            import boto3
        except ImportError:
            return {"uploaded": False, "reason": "missing_boto3"}

        s3_client = boto3.client("s3")

    s3_client.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=json.dumps(payload, indent=2),
        ContentType="application/json",
    )

    return {
        "uploaded": True,
        "bucket": bucket,
        "key": object_key,
        "s3_uri": f"s3://{bucket}/{object_key}",
    }
