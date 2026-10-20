import csv
import importlib.util
import json
from pathlib import Path


def load_evaluator():
    path = Path("claims-benchmark/evaluate_claims_results.py")
    spec = importlib.util.spec_from_file_location("claims_evaluator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_evaluator_keeps_outcomes_separate():
    output_path = Path("tests/.evaluator-output")
    outcomes = [
        {"id": "CE-VAL-01", "test": "a", "status": "passed", "duration_ms": 1, "severity": None, "detail": None},
        {"id": "CE-AUTH-01", "test": "b", "status": "failed", "duration_ms": 2, "severity": "Critical", "detail": "leak"},
        {"id": "CE-RES-01", "test": "c", "status": "could not run", "duration_ms": 0, "severity": "High", "detail": "offline"},
    ]
    (output_path / "raw-results.json").write_text(json.dumps({"exit_code": 1, "outcomes": outcomes}), encoding="utf-8")
    load_evaluator().evaluate(output_path)
    report = (output_path / "report.md").read_text(encoding="utf-8")
    assert "Passed: 1/3" in report
    assert "Failed: 1/3" in report
    assert "Could not run: 1/3" in report
    with (output_path / "outcomes.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["status"] for row in rows] == ["passed", "failed", "could not run"]
