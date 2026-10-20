import copy
import uuid

import pytest


@pytest.mark.ce_id("CE-VAL-01")
def test_valid_claim_is_accepted(clients, valid_claim):
    response = clients["claimant-a"].create_claim(valid_claim, f"val-{uuid.uuid4()}")
    assert response.status_code == 201
    assert response.json()["status"] == "SUBMITTED"


@pytest.mark.ce_id("CE-VAL-02,CE-VAL-03")
@pytest.mark.parametrize("mutation", ["missing", "wrong_type"])
def test_required_fields_and_types_are_rejected_without_a_record(clients, valid_claim, mutation):
    payload = copy.deepcopy(valid_claim)
    if mutation == "missing":
        del payload["patient_id"]
    else:
        payload["lines"][0]["amount"] = "not-a-number"
    before = len(clients["claimant-a"].list_claims().json())
    response = clients["claimant-a"].create_claim(payload, f"invalid-{uuid.uuid4()}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert len(clients["claimant-a"].list_claims().json()) == before


@pytest.mark.ce_id("CE-VAL-04,CE-VAL-07")
@pytest.mark.parametrize("field,value", [("amount", "0"), ("amount", "-1"), ("amount", "1.001"), ("status", "APPROVED")])
def test_boundaries_and_mass_assignment_are_rejected(clients, valid_claim, field, value):
    payload = copy.deepcopy(valid_claim)
    if field == "amount":
        payload["lines"][0][field] = value
    else:
        payload[field] = value
    response = clients["claimant-a"].create_claim(payload, f"boundary-{uuid.uuid4()}")
    assert response.status_code == 422


@pytest.mark.ce_id("CE-VAL-09")
def test_unknown_policy_is_structured_and_atomic(clients, valid_claim):
    payload = copy.deepcopy(valid_claim)
    payload["plan_id"] = 2147483647
    before = len(clients["claimant-a"].list_claims().json())
    response = clients["claimant-a"].create_claim(payload, f"policy-{uuid.uuid4()}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNKNOWN_POLICY"
    assert len(clients["claimant-a"].list_claims().json()) == before
