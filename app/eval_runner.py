import json
from pathlib import Path

from customer_support_tool import email_classifier
from report_generator import generate_html_report
from run_history import compare_runs, load_latest_run, save_timestamped_run
from s3_storage import upload_result_to_s3
from slack_alerts import send_slack_alert

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_CASES = BASE_DIR / "data" / "test_cases_v1.json"
ANSWERS = BASE_DIR / "data" / "answer_key_v1.json"
RUNS_DIR = BASE_DIR / "runs"
REPORTS_DIR = BASE_DIR / "reports"
MAX_CASES = 52

BASELINE_ACCURACY = None
WARNING_DROP_THRESHOLD = 0.03
CRITICAL_DROP_THRESHOLD = 0.08


def classify_regression(current_accuracy, baseline_accuracy):
    if baseline_accuracy is None:
        return {
            "status": "no_baseline",
            "accuracy_delta": None,
            "message": "No baseline accuracy configured yet."
        }

    accuracy_delta = baseline_accuracy - current_accuracy

    if accuracy_delta >= CRITICAL_DROP_THRESHOLD:
        status = "critical"
    elif accuracy_delta >= WARNING_DROP_THRESHOLD:
        status = "warning"
    else:
        status = "pass"

    return {
        "status": status,
        "accuracy_delta": accuracy_delta,
        "baseline_accuracy": baseline_accuracy,
        "current_accuracy": current_accuracy,
        "warning_threshold": WARNING_DROP_THRESHOLD,
        "critical_threshold": CRITICAL_DROP_THRESHOLD,
    }


def evaluation(max_cases=MAX_CASES, baseline_accuracy=BASELINE_ACCURACY):
    with open(TEST_CASES, "r", encoding="utf-8") as tests, open(ANSWERS, "r", encoding="utf-8") as answer_key:
        test_cases = json.load(tests)
        answers = json.load(answer_key)

    answers_by_id = {answer["id"]: answer for answer in answers}
    test_cases = test_cases[:max_cases]

    num_correct = 0
    num_run = 0
    failures = []
    case_results = []

    for test_case in test_cases:
        test_id = test_case["id"]
        email_to_send = test_case["email"]

        try:
            gemini_prediction = email_classifier(email_to_send)
        except Exception as error:
            print(f"Stopped on {test_id}: {error}")
            break

        num_run += 1
        correct_classification = answers_by_id[test_id]

        expected_category = correct_classification["category"]
        predicted_category = gemini_prediction["category"]
        correct = predicted_category == expected_category

        case_results.append({
            "id": test_id,
            "expected": expected_category,
            "predicted": predicted_category,
            "correct": correct,
        })

        if correct:
            num_correct += 1
        else:
            failures.append({
                "id": test_id,
                "expected": expected_category,
                "predicted": predicted_category,
            })

    accuracy = num_correct / num_run if num_run else 0
    regression = classify_regression(accuracy, baseline_accuracy)

    return {
        "status": regression["status"],
        "accuracy": accuracy,
        "accuracy_percent": f"{accuracy * 100:.2f}%",
        "num_correct": num_correct,
        "num_run": num_run,
        "num_requested": len(test_cases),
        "regression": regression,
        "failures": failures,
        "case_results": case_results,
    }


def write_result_to_file(payload):
    if not payload:
        return {"saved": False, "reason": "empty_payload"}

    results_path = BASE_DIR / "data" / "json_for_results001.json"
    with open(results_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2)

    return {"saved": True, "path": str(results_path)}


if __name__ == "__main__":
    previous_run = load_latest_run(RUNS_DIR)
    result = evaluation(MAX_CASES, BASELINE_ACCURACY)
    comparison = compare_runs(
        previous_run["payload"] if previous_run else None,
        result,
        WARNING_DROP_THRESHOLD,
        CRITICAL_DROP_THRESHOLD,
    )
    result["status"] = comparison["status"]
    result["regression"] = comparison["regression"]
    result["comparison"] = {
        "previous_run_path": previous_run["path"] if previous_run else None,
        "regressed_cases": comparison["regressed_cases"],
        "improved_cases": comparison["improved_cases"],
    }

    local_result = write_result_to_file(result)
    run_history_result = save_timestamped_run(result, RUNS_DIR)
    report_result = generate_html_report(result, REPORTS_DIR)
    result["report"] = report_result
    s3_result = upload_result_to_s3(result)
    alert_result = send_slack_alert(result)
    print(json.dumps({
        "evaluation": result,
        "local_result": local_result,
        "run_history": run_history_result,
        "html_report": report_result,
        "s3_upload": s3_result,
        "slack_alert": alert_result,
    }, indent=2))
