import json
from pathlib import Path

from customer_support_tool import email_classifier

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_CASES = BASE_DIR / "data" / "test_cases_v1.json"
ANSWERS = BASE_DIR / "data" / "answer_key_v1.json"
MAX_CASES = 10

def evaluation(max_cases=MAX_CASES):
    with open(TEST_CASES, "r", encoding="utf-8") as tests, open(ANSWERS, "r", encoding="utf-8") as answer_key:
        test_cases = json.load(tests)
        answers = json.load(answer_key)

    answers_by_id = {answer["id"]: answer for answer in answers}
    test_cases = test_cases[:max_cases]

    num_correct = 0
    num_run = 0

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

        if gemini_prediction["category"] == correct_classification["category"]:
            num_correct += 1

    if num_run == 0:
        return 0

    return num_correct / num_run


if __name__ == "__main__":
    print(evaluation(MAX_CASES))
