import json
import os
from urllib import error, request


DEFAULT_ALERT_STATUSES = {"warning", "critical"}


def _parse_alert_statuses(raw_statuses:str):
    if not raw_statuses:
        return DEFAULT_ALERT_STATUSES

    normalized = {status.strip().lower() for status in raw_statuses.split(",") if status.strip()}
    if "all" in normalized:
        return {"pass", "warning", "critical", "no_baseline"}

    return normalized


def should_send_alert(result, alert_statuses=None):
    status = result.get("status")
    statuses = alert_statuses if alert_statuses else DEFAULT_ALERT_STATUSES
    return status in statuses


def format_slack_message(result, project_name="Model Regression Detection System"):
    regression = result.get("regression", {})
    comparison = result.get("comparison", {})
    report = result.get("report", {})
    failures = result.get("failures", [])
    status = result.get("status", "unknown").upper()
    accuracy = result.get("accuracy_percent", "unknown")
    num_correct = result.get("num_correct", 0)
    num_run = result.get("num_run", 0)
    baseline = regression.get("baseline_accuracy")
    delta = regression.get("accuracy_delta")

    lines = [
        f"{project_name} eval status: {status}",
        f"Accuracy: {accuracy} ({num_correct}/{num_run})",
    ]

    if baseline is not None:
        lines.append(f"Baseline accuracy: {baseline * 100:.2f}%")

    if delta is not None:
        lines.append(f"Accuracy drop from baseline: {delta * 100:.2f}%")

    report_path = report.get("path")
    if report_path:
        lines.append(f"Report: {report_path}")

    regressed_cases = comparison.get("regressed_cases", [])
    if regressed_cases:
        preview = regressed_cases[:3]
        regressed_ids = ", ".join(case["id"] for case in preview)
        more_count = len(regressed_cases) - len(preview)
        suffix = f" (+{more_count} more)" if more_count > 0 else ""
        lines.append(f"Regressed cases: {regressed_ids}{suffix}")

    improved_cases = comparison.get("improved_cases", [])
    if improved_cases:
        preview = improved_cases[:3]
        improved_ids = ", ".join(case["id"] for case in preview)
        more_count = len(improved_cases) - len(preview)
        suffix = f" (+{more_count} more)" if more_count > 0 else ""
        lines.append(f"Improved cases: {improved_ids}{suffix}")

    if failures:
        preview = failures[:3]
        failed_ids = ", ".join(failure["id"] for failure in preview)
        more_count = len(failures) - len(preview)
        suffix = f" (+{more_count} more)" if more_count > 0 else ""
        lines.append(f"Failures: {failed_ids}{suffix}")

    return "\n".join(lines)


def send_slack_alert(result, webhook_url=None, alert_statuses=None, timeout=10):
    webhook = os.getenv("SLACK_WEBHOOK_URL") if webhook_url is None else webhook_url
    statuses = alert_statuses or _parse_alert_statuses(os.getenv("SLACK_ALERT_STATUSES"))

    if not webhook:
        return {"sent": False, "reason": "missing_webhook_url"}

    if not should_send_alert(result, statuses):
        return {"sent": False, "reason": "status_not_alertable", "status": result.get("status")}

    payload = {"text": format_slack_message(result)}
    encoded_payload = json.dumps(payload).encode("utf-8")
    slack_request = request.Request(
        webhook,
        data=encoded_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(slack_request, timeout=timeout) as response:
            return {"sent": True, "status_code": response.status}
    except error.HTTPError as exc:
        return {"sent": False, "reason": "http_error", "status_code": exc.code}
    except error.URLError as exc:
        return {"sent": False, "reason": "url_error", "details": str(exc.reason)}
