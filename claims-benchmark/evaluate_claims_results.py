import csv
import json
import sys
from collections import Counter
from pathlib import Path


def evaluate(run_dir: Path) -> None:
    raw_path = run_dir / "raw-results.json"
    raw = json.loads(raw_path.read_text(encoding="utf-8")) if raw_path.exists() else {
        "exit_code": 4,
        "outcomes": [{"id": "ALL", "test": "suite startup", "status": "could not run", "severity": "High", "detail": "No pytest result was produced"}],
    }
    outcomes = raw["outcomes"]
    (run_dir / "results.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    with (run_dir / "outcomes.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["id", "test", "status", "duration_ms", "severity", "detail"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(outcomes)
    counts = Counter(item["status"] for item in outcomes)
    lines = [
        "# Claims Engine benchmark report", "",
        f"Executed cases: {len(outcomes)}", "",
        f"- Passed: {counts['passed']}/{len(outcomes)}",
        f"- Failed: {counts['failed']}/{len(outcomes)}",
        f"- Could not run: {counts['could not run']}/{len(outcomes)}",
        "- Not applicable: 0/{}".format(len(outcomes)), "",
        "Results are not merged into a composite score.", "",
    ]
    performance = run_dir / "performance.json"
    if performance.exists():
        lines.extend(["## Performance", "", "```json", performance.read_text(encoding="utf-8"), "```", ""])
    failures = [item for item in outcomes if item["status"] != "passed"]
    if failures:
        lines.extend(["## Failures and unexecuted cases", ""])
        for item in failures:
            lines.append(f"- {item['id']}: {item['status']} ({item.get('severity') or 'unclassified'}) — {item.get('detail') or item['test']}")
    lines.extend([
        "", "## Limitations", "",
        "Synthetic users, policies, rules, and claims were used in one benchmark environment. These results do not validate real-world clinical, insurance-rule, or fraud-classification accuracy.",
    ])
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    evaluate(Path(sys.argv[1]))
