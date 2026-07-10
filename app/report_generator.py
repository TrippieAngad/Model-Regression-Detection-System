import html
from datetime import datetime, timezone
from pathlib import Path


def _escape(value):
    if value is None:
        return ""
    return html.escape(str(value))


def _format_percent(value):
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def _build_table(title, rows, columns):
    if not rows:
        return f"<section><h2>{_escape(title)}</h2><p>None.</p></section>"

    header_cells = "".join(f"<th>{_escape(label)}</th>" for label, _ in columns)
    body_rows = []

    for row in rows:
        cells = "".join(f"<td>{_escape(row.get(key))}</td>" for _, key in columns)
        body_rows.append(f"<tr>{cells}</tr>")

    return f"""
<section>
  <h2>{_escape(title)}</h2>
  <table>
    <thead><tr>{header_cells}</tr></thead>
    <tbody>
      {''.join(body_rows)}
    </tbody>
  </table>
</section>
"""


def generate_html_report(result, reports_dir, timestamp=None):
    if not result:
        return {"generated": False, "reason": "empty_payload"}

    reports_path = Path(reports_dir)
    reports_path.mkdir(parents=True, exist_ok=True)

    run_timestamp = timestamp or datetime.now(timezone.utc)
    formatted_timestamp = run_timestamp.strftime("%Y-%m-%d_%H-%M-%S")
    report_path = reports_path / f"eval_{formatted_timestamp}.html"

    regression = result.get("regression", {})
    comparison = result.get("comparison", {})
    failures = result.get("failures", [])
    regressed_cases = comparison.get("regressed_cases", [])
    improved_cases = comparison.get("improved_cases", [])

    failed_cases_table = _build_table(
        "Failed Cases",
        failures,
        [
            ("ID", "id"),
            ("Expected", "expected"),
            ("Predicted", "predicted"),
        ],
    )
    regressed_cases_table = _build_table(
        "Regressed Cases",
        regressed_cases,
        [
            ("ID", "id"),
            ("Expected", "expected"),
            ("Previous Prediction", "previous_predicted"),
            ("Current Prediction", "current_predicted"),
        ],
    )
    improved_cases_table = _build_table(
        "Improved Cases",
        improved_cases,
        [
            ("ID", "id"),
            ("Expected", "expected"),
            ("Previous Prediction", "previous_predicted"),
            ("Current Prediction", "current_predicted"),
        ],
    )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Model Regression Report</title>
  <style>
    body {{
      color: #1f2933;
      font-family: Arial, sans-serif;
      line-height: 1.45;
      margin: 32px;
      max-width: 1100px;
    }}
    .scorecard {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      margin: 20px 0;
    }}
    .metric {{
      border: 1px solid #d7dde5;
      border-radius: 6px;
      padding: 12px;
    }}
    .metric span {{
      color: #65758b;
      display: block;
      font-size: 13px;
      margin-bottom: 4px;
    }}
    table {{
      border-collapse: collapse;
      margin-bottom: 28px;
      width: 100%;
    }}
    th, td {{
      border: 1px solid #d7dde5;
      padding: 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: #f5f7fa;
    }}
    code {{
      background: #f5f7fa;
      padding: 2px 4px;
    }}
  </style>
</head>
<body>
  <h1>Model Regression Report</h1>
  <p><strong>Generated:</strong> {_escape(run_timestamp.isoformat())}</p>
  <p><strong>Previous run:</strong> <code>{_escape(comparison.get("previous_run_path") or "None")}</code></p>

  <section class="scorecard">
    <div class="metric"><span>Status</span><strong>{_escape(result.get("status", "unknown")).upper()}</strong></div>
    <div class="metric"><span>Accuracy</span><strong>{_escape(result.get("accuracy_percent", "unknown"))}</strong></div>
    <div class="metric"><span>Correct / Run</span><strong>{_escape(result.get("num_correct", 0))} / {_escape(result.get("num_run", 0))}</strong></div>
    <div class="metric"><span>Baseline Accuracy</span><strong>{_format_percent(regression.get("baseline_accuracy"))}</strong></div>
    <div class="metric"><span>Accuracy Drop</span><strong>{_format_percent(regression.get("accuracy_delta"))}</strong></div>
  </section>

  {regressed_cases_table}
  {improved_cases_table}
  {failed_cases_table}
</body>
</html>
"""

    report_path.write_text(page, encoding="utf-8")

    return {
        "generated": True,
        "path": str(report_path),
    }
