import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_WARNING_DROP_THRESHOLD = 0.03
DEFAULT_CRITICAL_DROP_THRESHOLD = 0.08


def build_run_filename(timestamp=None):
    run_timestamp = timestamp or datetime.now(timezone.utc)
    formatted_timestamp = run_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    return f"eval_{formatted_timestamp}.json"


def save_timestamped_run(payload, runs_dir, timestamp=None):
    if not payload:
        return {"saved": False, "reason": "empty_payload"}

    output_dir = Path(runs_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    run_path = output_dir / build_run_filename(timestamp)
    with open(run_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    return {"saved": True, "path": str(run_path)}


def load_latest_run(runs_dir):
    run_paths = sorted(Path(runs_dir).glob("eval_*.json"))
    if not run_paths:
        return None

    latest_path = run_paths[-1]
    with open(latest_path, "r", encoding="utf-8") as file:
        return {"path": str(latest_path), "payload": json.load(file)}


def _case_results_by_id(run_payload):
    return {
        case_result["id"]: case_result
        for case_result in run_payload.get("case_results", [])
    }


def _summarize_case_flip(case_id, previous_case, current_case):
    return {
        "id": case_id,
        "expected": current_case.get("expected"),
        "previous_predicted": previous_case.get("predicted"),
        "current_predicted": current_case.get("predicted"),
    }


def compare_runs(
    previous_run,
    current_run,
    warning_drop_threshold=DEFAULT_WARNING_DROP_THRESHOLD,
    critical_drop_threshold=DEFAULT_CRITICAL_DROP_THRESHOLD,
):
    current_accuracy = current_run.get("accuracy", 0)

    if previous_run is None:
        return {
            "status": "no_baseline",
            "regression": {
                "status": "no_baseline",
                "accuracy_delta": None,
                "baseline_accuracy": None,
                "current_accuracy": current_accuracy,
                "message": "No previous run found for comparison.",
            },
            "regressed_cases": [],
            "improved_cases": [],
        }

    previous_accuracy = previous_run.get("accuracy", 0)
    accuracy_delta = previous_accuracy - current_accuracy

    if accuracy_delta >= critical_drop_threshold:
        status = "critical"
    elif accuracy_delta >= warning_drop_threshold:
        status = "warning"
    else:
        status = "pass"

    previous_cases = _case_results_by_id(previous_run)
    current_cases = _case_results_by_id(current_run)
    regressed_cases = []
    improved_cases = []

    for case_id, current_case in current_cases.items():
        previous_case = previous_cases.get(case_id)
        if previous_case is None:
            continue

        was_correct = previous_case.get("correct", False)
        is_correct = current_case.get("correct", False)

        if was_correct and not is_correct:
            regressed_cases.append(_summarize_case_flip(case_id, previous_case, current_case))
        elif not was_correct and is_correct:
            improved_cases.append(_summarize_case_flip(case_id, previous_case, current_case))

    return {
        "status": status,
        "regression": {
            "status": status,
            "accuracy_delta": accuracy_delta,
            "baseline_accuracy": previous_accuracy,
            "current_accuracy": current_accuracy,
            "warning_threshold": warning_drop_threshold,
            "critical_threshold": critical_drop_threshold,
        },
        "regressed_cases": regressed_cases,
        "improved_cases": improved_cases,
    }
