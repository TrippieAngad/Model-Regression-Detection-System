import unittest

from app.slack_alerts import format_slack_message, send_slack_alert, should_send_alert


class SlackAlertsTest(unittest.TestCase):
    def test_warning_status_is_alertable_by_default(self):
        self.assertTrue(should_send_alert({"status": "warning"}))

    def test_pass_status_is_not_alertable_by_default(self):
        self.assertFalse(should_send_alert({"status": "pass"}))

    def test_missing_webhook_skips_send(self):
        result = {"status": "critical"}

        alert_result = send_slack_alert(result, webhook_url="")

        self.assertEqual(alert_result["reason"], "missing_webhook_url")
        self.assertFalse(alert_result["sent"])

    def test_message_includes_core_eval_metrics(self):
        result = {
            "status": "critical",
            "accuracy_percent": "86.54%",
            "num_correct": 45,
            "num_run": 52,
            "regression": {
                "baseline_accuracy": 0.95,
                "accuracy_delta": 0.0846,
            },
            "failures": [
                {"id": "edge_001", "expected": "technical", "predicted": "academics"},
            ],
            "comparison": {
                "regressed_cases": [
                    {"id": "billing_009"},
                ],
                "improved_cases": [
                    {"id": "spam_004"},
                ],
            },
        }

        message = format_slack_message(result)

        self.assertIn("CRITICAL", message)
        self.assertIn("86.54%", message)
        self.assertIn("45/52", message)
        self.assertIn("edge_001", message)
        self.assertIn("billing_009", message)
        self.assertIn("spam_004", message)


if __name__ == "__main__":
    unittest.main()
