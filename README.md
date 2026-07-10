# Model-Regression-Detection-System
CI/CD-style LLM evaluation system that tests prompt and model changes against golden datasets to detect regressions before deployment.

## Slack Alerts

The evaluator can send a Slack alert when a run detects a regression. Alerts are sent through a Slack incoming webhook, so the app does not need the full Slack SDK.

### 1. Create the Slack webhook

1. Go to Slack API apps and create a new app for your workspace.
2. Enable **Incoming Webhooks**.
3. Add a webhook to the channel where regression alerts should appear.
4. Copy the webhook URL.

### 2. Add environment variables

Create or update `.env`:

```bash
GEMINI_KEY=your_gemini_key
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
SLACK_ALERT_STATUSES=warning,critical
```

`SLACK_ALERT_STATUSES` is optional. By default, only `warning` and `critical` runs send alerts. Use `all` if you want Slack messages for every evaluation run while testing.

### 3. Run the evaluator

```bash
python app/eval_runner.py
```

The script writes the latest JSON result to `data/json_for_results001.json`, saves a timestamped copy in `runs/`, compares the current run against the previous timestamped run, generates an HTML report in `reports/`, and then attempts to send a Slack alert. If `SLACK_WEBHOOK_URL` is missing, the evaluator still completes and reports that the Slack alert was skipped.

### 4. Test the Slack alert helpers

```bash
python -m unittest tests/test_slack_alerts.py
```

## S3 Eval Result Storage

The evaluator can also upload each JSON result to S3. This gives CI/CD runs a durable history that can later power trend reports, HTML report links, and Terraform-managed infrastructure.

### 1. Add AWS settings

Create an S3 bucket for eval artifacts, then add the bucket name to `.env`:

```bash
S3_EVAL_BUCKET=your-eval-results-bucket
AWS_REGION=us-east-1
```

Your local shell or CI runner also needs AWS credentials with permission to call `s3:PutObject` on that bucket. If `S3_EVAL_BUCKET` is missing, the evaluator still completes and reports that S3 upload was skipped.

### 2. Run the evaluator

```bash
python app/eval_runner.py
```

When configured, each result is uploaded under:

```text
runs/eval_YYYY-MM-DD_HH-MM-SS.json
```

### 3. Test the S3 upload helpers

```bash
python -m unittest tests/test_s3_storage.py
```

## Previous-Run Regression Comparison

Each eval run is saved locally under:

```text
runs/eval_YYYY-MM-DD_HH-MM-SS.json
```

Before saving the current run, the evaluator loads the latest existing run from `runs/` and compares it to the current result. The comparison records:

- accuracy drop from the previous run
- regressed cases that flipped from correct to wrong
- improved cases that flipped from wrong to correct
- `pass`, `warning`, `critical`, or `no_baseline` status

The first run will use `no_baseline` because there is no prior run to compare against. Generated run JSON files are ignored by git via `.gitignore`.

Test the run-history helpers with:

```bash
python -m unittest tests/test_run_history.py
```

## HTML Reports

Each eval run generates a human-readable report under:

```text
reports/eval_YYYY-MM-DD_HH-MM-SS.html
```

The report includes:

- status and accuracy scorecard
- previous run path
- baseline accuracy and accuracy drop
- regressed cases
- improved cases
- failed cases

The Slack alert includes the local report path when a report is generated. Generated report files are ignored by git via `.gitignore`.

Test the report generator with:

```bash
python -m unittest tests/test_report_generator.py
```

## Docker

The evaluator can run inside a Docker container for repeatable local, CI, and cloud execution.

### 1. Build the image

```bash
docker build -t model-regression-evaluator .
```

### 2. Run the test suite in the image

```bash
docker run --rm model-regression-evaluator python -m unittest discover -s tests
```

### 3. Run the evaluator

```bash
docker run --rm --env-file .env model-regression-evaluator
```

Running the evaluator container will call Gemini and may send Slack alerts or upload to S3 depending on the variables configured in `.env`.
