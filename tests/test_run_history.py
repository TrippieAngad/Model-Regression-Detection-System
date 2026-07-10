import tempfile
import unittest
from datetime import datetime, timezone

from app.run_history import compare_runs, load_latest_run, save_timestamped_run


class RunHistoryTest(unittest.TestCase):
    def test_save_and_load_latest_run(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            older_timestamp = datetime(2026, 7, 9, 12, 0, 0, tzinfo=timezone.utc)
            newer_timestamp = datetime(2026, 7, 9, 13, 0, 0, tzinfo=timezone.utc)

            save_timestamped_run({"accuracy": 0.5}, tmp_dir, older_timestamp)
            save_timestamped_run({"accuracy": 0.75}, tmp_dir, newer_timestamp)

            latest_run = load_latest_run(tmp_dir)

            self.assertEqual(latest_run["payload"]["accuracy"], 0.75)
            self.assertTrue(latest_run["path"].endswith("eval_2026-07-09_13-00-00.json"))

    def test_compare_runs_detects_regressions_and_improvements(self):
        previous = {
            "accuracy": 0.75,
            "case_results": [
                {"id": "case_1", "expected": "billing", "predicted": "billing", "correct": True},
                {"id": "case_2", "expected": "spam", "predicted": "billing", "correct": False},
                {"id": "case_3", "expected": "technical", "predicted": "technical", "correct": True},
                {"id": "case_4", "expected": "academics", "predicted": "spam", "correct": False},
            ],
        }
        current = {
            "accuracy": 0.5,
            "case_results": [
                {"id": "case_1", "expected": "billing", "predicted": "technical", "correct": False},
                {"id": "case_2", "expected": "spam", "predicted": "spam", "correct": True},
                {"id": "case_3", "expected": "technical", "predicted": "technical", "correct": True},
                {"id": "case_4", "expected": "academics", "predicted": "billing", "correct": False},
            ],
        }

        comparison = compare_runs(previous, current)

        self.assertEqual(comparison["status"], "critical")
        self.assertEqual(comparison["regressed_cases"][0]["id"], "case_1")
        self.assertEqual(comparison["improved_cases"][0]["id"], "case_2")

    def test_compare_without_previous_run_uses_no_baseline(self):
        comparison = compare_runs(None, {"accuracy": 1.0, "case_results": []})

        self.assertEqual(comparison["status"], "no_baseline")
        self.assertEqual(comparison["regression"]["baseline_accuracy"], None)
        self.assertEqual(comparison["regressed_cases"], [])


if __name__ == "__main__":
    unittest.main()
