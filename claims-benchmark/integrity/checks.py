def check_public_integrity(client) -> list[str]:
    """Return invariant violations observable through the public API."""
    response = client.list_claims()
    response.raise_for_status()
    claims = response.json()
    violations = []
    ids = [claim["id"] for claim in claims]
    if len(ids) != len(set(ids)):
        violations.append("duplicate claim identifiers")
    valid_states = {"PENDING_RULES", "PENDING_FRAUD", "FAILED_ASSESSMENT", "REVIEW", "HUMAN_REVIEW", "SUBMITTED", "APPROVED", "DENIED", "PAID", "CLOSED"}
    for claim in claims:
        if claim["status"] not in valid_states:
            violations.append(f"claim {claim['id']} has invalid state {claim['status']}")
        audit = client.request("GET", f"/api/v1/claims/{claim['id']}/audit")
        if audit.status_code != 200 or not audit.json():
            violations.append(f"claim {claim['id']} has no public audit trail")
    return violations
