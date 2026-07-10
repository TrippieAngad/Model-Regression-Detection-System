import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app.report_generator import generate_html_report


class ReportGeneratorTest(unittest.TestCase):
    def test_generate_html_report_writes_report_file(self):
        result = {
            "status": "critical",
            "accuracy_percent": "86.54%",
            "num_correct": 45,
            "num_run": 52,
            "regression": {
                "baseline_accuracy": 0.95,
                "accuracy_delta": 0.0846,
            },
            "comparison": {
                "previous_run_path": "runs/eval_previous.json",
                "regressed_cases": [
                    {
                        "id": "billing_009",
                        "expected": "billing",
                        "previous_predicted": "billing",
                        "current_predicted": "technical",
                    },
                ],
                "improved_cases": [],
            },
            "failures": [
                {"id": "edge_001", "expected": "technical", "predicted": "academics"},
            ],
        }
        timestamp = datetime(2026, 7, 9, 14, 30, 5, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_result = generate_html_report(result, tmp_dir, timestamp)

            self.assertTrue(report_result["generated"])
            report_path = Path(report_result["path"])
            self.assertEqual(report_path.name, "eval_2026-07-09_14-30-05.html")

            report_html = report_path.read_text(encoding="utf-8")
            self.assertIn("Model Regression Report", report_html)
            self.assertIn("CRITICAL", report_html)
            self.assertIn("86.54%", report_html)
            self.assertIn("billing_009", report_html)
            self.assertIn("edge_001", report_html)


if __name__ == "__main__":
    unittest.main()
