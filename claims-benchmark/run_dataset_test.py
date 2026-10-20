import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from dataset_adapters.mobeen_fatimaa import inspect_csv, map_row, seeded_stratified_sample


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--config", type=Path, default=ROOT / "config.example.json")
    parser.add_argument("--sample-size", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    health = httpx.get(f"{config['base_url']}/health", timeout=3)
    if health.status_code != 200 or health.json().get("environment") != "benchmark":
        raise SystemExit("REFUSED: target does not report environment=benchmark")
    login = httpx.post(f"{config['base_url']}/api/v1/auth/login", data={"username": "claimant-a@benchmark.test", "password": config["password"]}, timeout=5)
    login.raise_for_status()
    auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
    patient = httpx.post(f"{config['base_url']}/api/v1/patients", headers=auth, json={
        "first_name": "External", "last_name": "Synthetic", "dob": "1985-01-01", "gender": "other", "province": "AB",
        "insurance": {"payer_id": "AHCIP", "member_id": f"EXT-{time.time_ns()}", "health_card_number": "123456789", "effective_date": "2024-01-01"},
    }, timeout=10)
    patient.raise_for_status()
    patient_id = patient.json()["patient_id"]
    source_profile = inspect_csv(args.csv)
    rows = seeded_stratified_sample(args.csv, args.sample_size, args.seed)

    def submit(row):
        payload, metadata = map_row(row, patient_id=patient_id, plan_id=config["plan_id"])
        started = time.perf_counter()
        try:
            response = httpx.post(f"{config['base_url']}/api/v1/claims", headers={**auth, "Idempotency-Key": metadata["idempotency_key"]}, json=payload, timeout=config["request_timeout_seconds"])
            body = response.json()
            structured = response.status_code < 400 or isinstance(body.get("error"), dict)
            return {"source_claim_id": metadata["source_claim_id"], "status_code": response.status_code, "structured": structured, "latency_ms": round((time.perf_counter() - started) * 1000, 3), "claim_id": body.get("id")}
        except httpx.TimeoutException:
            return {"source_claim_id": metadata["source_claim_id"], "status_code": 0, "structured": False, "latency_ms": round((time.perf_counter() - started) * 1000, 3), "timeout": True}

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        outcomes = list(pool.map(submit, rows))
    # Controlled mutation: required amount removed and must produce a structured 422.
    corrupt_payload, corrupt_meta = map_row(rows[0], patient_id=patient_id, plan_id=config["plan_id"])
    del corrupt_payload["lines"][0]["amount"]
    corrupted = httpx.post(f"{config['base_url']}/api/v1/claims", headers={**auth, "Idempotency-Key": f"{corrupt_meta['idempotency_key']}-corrupt"}, json=corrupt_payload, timeout=5)
    # Repeating an accepted row must return the same record.
    first_accepted = next((item for item in outcomes if item["status_code"] in (200, 201)), None)
    idempotency_ok = None
    if first_accepted:
        replay = submit(next(row for row in rows if row["claim_id"] == first_accepted["source_claim_id"]))
        idempotency_ok = replay.get("claim_id") == first_accepted.get("claim_id") and replay["status_code"] == 200
    report = {
        "dataset": "MobeenFatimaa/Insurance-Claim-Fraud-Detection-Dataset-Generator",
        "commit": "2551a1c77275464906f65daabcd6d208b7d33c32", "licence": "Apache-2.0", "synthetic": True,
        "source_profile": source_profile, "sample_size": len(rows), "seed": args.seed,
        "mapping_coverage": "5/62 (8.1%)", "synthetic_fill_target_fields": 7,
        "accepted": sum(item["status_code"] in (200, 201) for item in outcomes),
        "structured_rejections": sum(item["status_code"] >= 400 and item["structured"] for item in outcomes),
        "server_errors": sum(item["status_code"] >= 500 or item["status_code"] == 0 for item in outcomes),
        "controlled_mutation_passed": corrupted.status_code == 422 and isinstance(corrupted.json().get("error"), dict),
        "idempotency_replay_passed": idempotency_ok,
        "outcomes": outcomes,
        "limitation": "Synthetic motor claims mapped to health claims; fraud labels were not evaluated and results do not validate real-world behavior.",
    }
    run_dir = ROOT / "results" / ("dataset-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    run_dir.mkdir(parents=True)
    (run_dir / "dataset-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(run_dir)
    return 0 if report["server_errors"] == 0 and report["controlled_mutation_passed"] and report["idempotency_replay_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
