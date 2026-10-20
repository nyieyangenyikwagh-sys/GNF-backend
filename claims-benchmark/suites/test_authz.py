import uuid

import pytest


@pytest.mark.ce_id("CE-AUTH-01,CE-AUTH-03")
def test_other_claimant_cannot_read_or_list_claim(clients, valid_claim):
    claim = clients["claimant-a"].create_claim(valid_claim, f"auth-{uuid.uuid4()}").json()
    assert clients["claimant-b"].get_claim(claim["id"]).status_code == 404
    assert claim["id"] not in {item["id"] for item in clients["claimant-b"].list_claims().json()}


@pytest.mark.ce_id("CE-AUTH-02,CE-AUTH-05")
@pytest.mark.parametrize("actor", ["claimant-a", "auditor"])
def test_claimant_and_auditor_cannot_take_manual_action(clients, valid_claim, actor):
    claim = clients["claimant-a"].create_claim(valid_claim, f"auth-write-{uuid.uuid4()}").json()
    assert clients[actor].transition(claim["id"], "APPROVED").status_code == 403


@pytest.mark.ce_id("CE-AUTH-04")
def test_missing_and_bad_tokens_are_401(config):
    import httpx
    assert httpx.get(f"{config['base_url']}/api/v1/claims").status_code == 401
    assert httpx.get(f"{config['base_url']}/api/v1/claims", headers={"Authorization": "Bearer broken"}).status_code == 401


@pytest.mark.ce_id("CE-AUTH-06")
def test_claimant_response_hides_internal_assessment_fields(clients, valid_claim):
    body = clients["claimant-a"].create_claim(valid_claim, f"exposure-{uuid.uuid4()}").json()
    assert not ({"fraud_result", "fraud_score", "rules_result", "owner_user_id"} & body.keys())
