import uuid

import pytest


@pytest.mark.ce_id("CE-AUD-01")
def test_audit_is_ordered_complete_and_correlated(clients, valid_claim):
    correlation_id = f"bench-{uuid.uuid4()}"
    response = clients["claimant-a"].request(
        "POST", "/api/v1/claims", json=valid_claim,
        headers={"Idempotency-Key": f"audit-{uuid.uuid4()}", "X-Correlation-ID": correlation_id},
    )
    assert response.status_code == 201
    claim = response.json()
    events = clients["auditor"].request("GET", f"/api/v1/claims/{claim['id']}/audit").json()
    actions = [event["action"] for event in events]
    assert actions[0] == "claim.created"
    assert "rules.completed" in actions and "fraud.completed" in actions
    assert actions.count("claim.status_changed") == 2
    assert all(event["correlation_id"] == correlation_id for event in events)
    assert [event["claim_version"] for event in events] == sorted(event["claim_version"] for event in events)
