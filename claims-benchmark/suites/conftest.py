import json
import os
import sys
import uuid
from datetime import date
from pathlib import Path

import httpx
import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCHMARK_ROOT))
from adapters.claims_client import ClaimsClient


RESULTS = []


def pytest_configure(config):
    config.addinivalue_line("markers", "ce_id(value): Claims Engine benchmark case ID")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    marker = item.get_closest_marker("ce_id")
    ids = marker.args[0].split(",") if marker else [item.nodeid]
    status = "passed" if report.passed else "failed" if report.failed else "could not run"
    for case_id in ids:
        RESULTS.append({
            "id": case_id.strip(), "test": item.nodeid, "status": status,
            "duration_ms": round(report.duration * 1000, 3),
            "severity": "Critical" if case_id.startswith("CE-AUTH") and report.failed else "High" if report.failed else None,
            "detail": str(report.longrepr)[:2000] if report.failed else None,
        })


def pytest_sessionfinish(session, exitstatus):
    output = os.getenv("CLAIMS_RESULTS_FILE")
    if output:
        Path(output).write_text(json.dumps({"exit_code": exitstatus, "outcomes": RESULTS}, indent=2), encoding="utf-8")


@pytest.fixture(scope="session")
def config():
    path = Path(os.getenv("CLAIMS_BENCHMARK_CONFIG", BENCHMARK_ROOT / "config.json"))
    if not path.exists():
        path = BENCHMARK_ROOT / "config.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session", autouse=True)
def benchmark_interlock(config):
    try:
        response = httpx.get(f"{config['base_url']}/health", timeout=3)
    except httpx.HTTPError as exc:
        pytest.exit(f"COULD NOT RUN: target unavailable: {exc}", returncode=4)
    if response.status_code != 200 or response.json().get("environment") != "benchmark":
        pytest.exit("REFUSED: target does not report environment=benchmark", returncode=5)


@pytest.fixture(scope="session")
def clients(config):
    result = {}
    for name in ("claimant-a", "claimant-b", "adjuster", "supervisor", "auditor", "service"):
        client = ClaimsClient(config["base_url"], timeout=config["request_timeout_seconds"])
        client.login(f"{name}@benchmark.test", config["password"])
        result[name] = client
    return result


@pytest.fixture(scope="session")
def reference_data(config, clients):
    member = f"MEM-{uuid.uuid4().hex[:10]}"
    response = clients["claimant-a"].request("POST", "/api/v1/patients", json={
        "first_name": "Synthetic", "last_name": "ClaimantA", "dob": "1990-05-01",
        "gender": "other", "province": "AB",
        "insurance": {"payer_id": "AHCIP", "member_id": member, "health_card_number": "123456789", "effective_date": "2024-01-01"},
    })
    assert response.status_code == 201, response.text
    body = response.json()
    return {"patient_id": body["patient_id"], "insurance_id": body["patient_insurance_id"], "plan_id": config["plan_id"]}


@pytest.fixture
def valid_claim(reference_data):
    return {
        "patient_id": reference_data["patient_id"], "plan_id": reference_data["plan_id"],
        "province": "AB", "provider_billing_number": "123456", "service_date": date.today().isoformat(),
        "lines": [{"service_code": "03.03A", "diagnosis_code": "J06.9", "units": 1, "amount": "85.00"}],
    }


@pytest.fixture
def set_stub(config):
    changed = []

    def setter(dependency: str, mode: str):
        response = httpx.put(
            f"{config['stub_url']}/__control/{dependency}/{mode}",
            headers={"Authorization": f"Bearer {config['stub_control_token']}"}, timeout=3,
        )
        response.raise_for_status()
        changed.append(dependency)

    yield setter
    for dependency in set(changed):
        setter(dependency, "success")
