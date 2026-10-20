import uuid

import pytest


@pytest.mark.ce_id("CE-RES-01,CE-RES-03,CE-RES-05")
@pytest.mark.parametrize("mode", ["error", "invalid", "timeout"])
def test_rules_fault_is_never_eligibility_success(clients, valid_claim, set_stub, mode):
    set_stub("rules", mode)
    response = clients["claimant-a"].create_claim(valid_claim, f"rules-{mode}-{uuid.uuid4()}")
    assert response.status_code == 201
    assert response.json()["status"] == "FAILED_ASSESSMENT"


@pytest.mark.ce_id("CE-RES-02,CE-RES-04")
@pytest.mark.parametrize("mode", ["error", "invalid"])
def test_fraud_fault_is_never_treated_as_clean(clients, valid_claim, set_stub, mode):
    set_stub("fraud", mode)
    response = clients["claimant-a"].create_claim(valid_claim, f"fraud-{mode}-{uuid.uuid4()}")
    assert response.status_code == 201
    assert response.json()["status"] == "FAILED_ASSESSMENT"


@pytest.mark.ce_id("CE-RES-08")
def test_dependency_recovery_can_resume_failed_claim(clients, valid_claim, set_stub):
    set_stub("rules", "error")
    claim = clients["claimant-a"].create_claim(valid_claim, f"recover-{uuid.uuid4()}").json()
    assert claim["status"] == "FAILED_ASSESSMENT"
    set_stub("rules", "success")
    response = clients["service"].request("POST", f"/api/v1/claims/{claim['id']}/retry-assessment")
    assert response.status_code == 200
    assert response.json()["status"] == "SUBMITTED"


@pytest.mark.ce_id("CE-RES-09")
def test_correlation_id_round_trip(clients, valid_claim):
    correlation_id = f"correlation-{uuid.uuid4()}"
    response = clients["claimant-a"].request(
        "POST", "/api/v1/claims", json=valid_claim,
        headers={"Idempotency-Key": f"corr-{uuid.uuid4()}", "X-Correlation-ID": correlation_id},
    )
    assert response.headers["X-Correlation-ID"] == correlation_id
    events = clients["auditor"].request("GET", f"/api/v1/claims/{response.json()['id']}/audit").json()
    assert {event["correlation_id"] for event in events} == {correlation_id}
