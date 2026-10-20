import copy
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.mark.ce_id("CE-IDEM-01")
def test_same_key_returns_one_record(clients, valid_claim):
    key = f"idem-{uuid.uuid4()}"
    first = clients["claimant-a"].create_claim(valid_claim, key)
    second = clients["claimant-a"].create_claim(valid_claim, key)
    assert first.status_code == 201
    assert second.status_code == 200
    assert second.headers["Idempotent-Replay"] == "true"
    assert first.json()["id"] == second.json()["id"]


@pytest.mark.ce_id("CE-IDEM-02")
def test_same_key_different_payload_conflicts(clients, valid_claim):
    key = f"idem-conflict-{uuid.uuid4()}"
    assert clients["claimant-a"].create_claim(valid_claim, key).status_code == 201
    changed = copy.deepcopy(valid_claim)
    changed["lines"][0]["amount"] = "86.00"
    response = clients["claimant-a"].create_claim(changed, key)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


@pytest.mark.ce_id("CE-IDEM-03")
def test_simultaneous_identical_requests_create_exactly_one(clients, valid_claim):
    key = f"idem-race-{uuid.uuid4()}"
    with ThreadPoolExecutor(max_workers=5) as pool:
        responses = list(pool.map(lambda _: clients["claimant-a"].create_claim(valid_claim, key), range(5)))
    assert {response.status_code for response in responses} <= {200, 201}
    assert len({response.json()["id"] for response in responses}) == 1


@pytest.mark.ce_id("CE-IDEM-06")
def test_stale_update_is_rejected(clients, valid_claim):
    claim = clients["claimant-a"].create_claim(valid_claim, f"version-{uuid.uuid4()}").json()
    response = clients["claimant-a"].request(
        "PATCH", f"/api/v1/claims/{claim['id']}", headers={"If-Match": str(claim["version"] - 1)},
        json={"provider_billing_number": "123456"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "VERSION_CONFLICT"
