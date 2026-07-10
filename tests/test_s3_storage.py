import json
import unittest
from datetime import datetime, timezone

from app.s3_storage import build_eval_result_key, upload_result_to_s3


class FakeS3Client:
    def __init__(self):
        self.put_object_calls = []

    def put_object(self, **kwargs):
        self.put_object_calls.append(kwargs)


class S3StorageTest(unittest.TestCase):
    def test_build_eval_result_key_uses_utc_timestamp(self):
        timestamp = datetime(2026, 7, 9, 14, 30, 5, tzinfo=timezone.utc)

        key = build_eval_result_key(timestamp)

        self.assertEqual(key, "runs/eval_2026-07-09_14-30-05.json")

    def test_missing_bucket_skips_upload(self):
        result = upload_result_to_s3({"status": "pass"}, bucket_name="")

        self.assertFalse(result["uploaded"])
        self.assertEqual(result["reason"], "missing_bucket")

    def test_upload_writes_json_payload_to_s3(self):
        fake_client = FakeS3Client()
        payload = {"status": "critical", "accuracy": 0.86}

        result = upload_result_to_s3(
            payload,
            bucket_name="model-eval-results",
            key="runs/eval_test.json",
            s3_client=fake_client,
        )

        self.assertTrue(result["uploaded"])
        self.assertEqual(result["s3_uri"], "s3://model-eval-results/runs/eval_test.json")
        self.assertEqual(len(fake_client.put_object_calls), 1)

        call = fake_client.put_object_calls[0]
        self.assertEqual(call["Bucket"], "model-eval-results")
        self.assertEqual(call["Key"], "runs/eval_test.json")
        self.assertEqual(call["ContentType"], "application/json")
        self.assertEqual(json.loads(call["Body"]), payload)


if __name__ == "__main__":
    unittest.main()
