import json
import math
import os
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parent


def percentile(values, fraction):
    if not values:
        return None
    return sorted(values)[min(len(values) - 1, math.ceil(len(values) * fraction) - 1)]


def load_config():
    path = Path(os.getenv("CLAIMS_BENCHMARK_CONFIG", ROOT / "config.json"))
    if not path.exists():
        path = ROOT / "config.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


def interlock(config):
    response = httpx.get(f"{config['base_url']}/health", timeout=3)
    if response.status_code != 200 or response.json().get("environment") != "benchmark":
        raise RuntimeError("runner refused target: /health must report environment=benchmark")


def token(config, email):
    response = httpx.post(f"{config['base_url']}/api/v1/auth/login", data={"username": email, "password": config["password"]}, timeout=5)
    response.raise_for_status()
    return response.json()["access_token"]


def run_performance(config, run_dir):
    auth = {"Authorization": f"Bearer {token(config, 'claimant-a@benchmark.test')}"}
    patient = httpx.post(f"{config['base_url']}/api/v1/patients", headers=auth, json={
        "first_name": "Load", "last_name": "Synthetic", "dob": "1980-01-01", "gender": "other", "province": "AB",
        "insurance": {"payer_id": "AHCIP", "member_id": f"LOAD-{time.time_ns()}", "health_card_number": "123456789", "effective_date": "2024-01-01"},
    }, timeout=10)
    patient.raise_for_status()
    patient_id = patient.json()["patient_id"]
    payload = {"patient_id": patient_id, "plan_id": config["plan_id"], "province": "AB", "provider_billing_number": "123456", "service_date": date.today().isoformat(), "lines": [{"service_code": "03.03A", "diagnosis_code": "J06.9", "units": 1, "amount": "85.00"}]}

    def submit(index):
        started = time.perf_counter()
        try:
            response = httpx.post(f"{config['base_url']}/api/v1/claims", headers={**auth, "Idempotency-Key": f"perf-{time.time_ns()}-{index}"}, json=payload, timeout=config["request_timeout_seconds"])
            return (time.perf_counter() - started) * 1000, response.status_code, False
        except httpx.TimeoutException:
            return (time.perf_counter() - started) * 1000, 0, True

    for index in range(3):
        submit(f"warmup-{index}")
    rows = []
    request_count = config.get("performance_requests", 25)
    for concurrency in (1, 5, 10, 25):
        for repeat in range(2):
            started = time.perf_counter()
            with ThreadPoolExecutor(max_workers=concurrency) as pool:
                samples = list(pool.map(submit, range(request_count)))
            elapsed = time.perf_counter() - started
            latencies = [sample[0] for sample in samples]
            errors = sum(sample[1] >= 400 or sample[1] == 0 for sample in samples)
            timeouts = sum(sample[2] for sample in samples)
            rows.append({"concurrency": concurrency, "repeat": repeat + 1, "requests": request_count, "median_ms": round(statistics.median(latencies), 2), "p95_ms": round(percentile(latencies, .95), 2), "p99_ms": round(percentile(latencies, .99), 2), "throughput_rps": round(request_count / elapsed, 2), "error_rate": errors / request_count, "timeout_rate": timeouts / request_count})
    (run_dir / "performance.json").write_text(json.dumps({"warmup_excluded": 3, "container_limits": "not configured", "runs": rows}, indent=2), encoding="utf-8")


def main():
    config = load_config()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = ROOT / "results" / run_id
    run_dir.mkdir(parents=True)
    raw = run_dir / "raw-results.json"
    try:
        interlock(config)
    except Exception as exc:
        raw.write_text(json.dumps({"exit_code": 5, "outcomes": [{"id": "ALL", "test": "environment interlock", "status": "could not run", "severity": "High", "detail": str(exc)}]}, indent=2), encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "evaluate_claims_results.py"), str(run_dir)], check=False)
        return 5
    env = os.environ.copy()
    env["CLAIMS_RESULTS_FILE"] = str(raw)
    completed = subprocess.run([sys.executable, "-m", "pytest", str(ROOT / "suites"), "-q"], env=env, check=False)
    try:
        run_performance(config, run_dir)
    except Exception as exc:
        (run_dir / "performance.json").write_text(json.dumps({"status": "could not run", "detail": str(exc)}, indent=2), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "evaluate_claims_results.py"), str(run_dir)], check=False)
    print(run_dir)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
