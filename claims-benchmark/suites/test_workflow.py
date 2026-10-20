import uuid

import pytest


@pytest.mark.ce_id("CE-WF-01")
def test_happy_path(clients, valid_claim):
    response = clients["claimant-a"].create_claim(valid_claim, f"wf-{uuid.uuid4()}")
    assert response.status_code == 201
    assert response.json()["status"] == "SUBMITTED"


@pytest.mark.ce_id("CE-WF-02")
def test_rule_failure_routes_to_review(clients, valid_claim, set_stub):
    set_stub("rules", "rule_fail")
    response = clients["claimant-a"].create_claim(valid_claim, f"rule-fail-{uuid.uuid4()}")
    assert response.status_code == 201
    assert response.json()["status"] == "REVIEW"
    assert response.json()["denial_reason_code"] == "STUB_RULE_FAIL"


@pytest.mark.ce_id("CE-WF-03")
def test_high_fraud_risk_never_auto_rejects(clients, valid_claim, set_stub):
    set_stub("fraud", "high_risk")
    response = clients["claimant-a"].create_claim(valid_claim, f"fraud-high-{uuid.uuid4()}")
    assert response.status_code == 201
    assert response.json()["status"] == "REVIEW"


@pytest.mark.ce_id("CE-WF-05")
def test_illegal_transition_leaves_state_unchanged(clients, valid_claim):
    created = clients["claimant-a"].create_claim(valid_claim, f"illegal-{uuid.uuid4()}").json()
    response = clients["adjuster"].transition(created["id"], "CLOSED")
    assert response.status_code == 409
    assert clients["adjuster"].get_claim(created["id"]).json()["status"] == "SUBMITTED"
