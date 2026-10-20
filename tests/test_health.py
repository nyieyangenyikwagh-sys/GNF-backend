from datetime import date
from decimal import Decimal
import importlib.util
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas.claim import ClaimCreate, FraudDecision, RulesDecision
from app.services.claim_status import ALLOWED_TRANSITIONS


def valid_payload():
    return {
        "patient_id": 1,
        "plan_id": 1,
        "province": "ab",
        "provider_billing_number": "123456",
        "service_date": date.today().isoformat(),
        "lines": [{"service_code": "03.03A", "diagnosis_code": "J06.9", "units": 1, "amount": "85.00"}],
    }


def test_claim_schema_normalizes_and_preserves_decimal():
    claim = ClaimCreate.model_validate(valid_payload())
    assert claim.province == "AB"
    assert claim.lines[0].amount == Decimal("85.00")


@pytest.mark.parametrize("field,value", [("amount", "0"), ("amount", "1.001"), ("units", 0)])
def test_claim_schema_rejects_amount_and_unit_boundaries(field, value):
    payload = valid_payload()
    payload["lines"][0][field] = value
    with pytest.raises(ValidationError):
        ClaimCreate.model_validate(payload)


def test_claim_schema_forbids_mass_assignment():
    payload = valid_payload()
    payload["status"] = "APPROVED"
    with pytest.raises(ValidationError):
        ClaimCreate.model_validate(payload)


def test_dependency_contracts_reject_invalid_defaults():
    with pytest.raises(ValidationError):
        RulesDecision.model_validate({"schema_version": "1.0", "outcome": "PASS"})
    with pytest.raises(ValidationError):
        FraudDecision.model_validate({"schema_version": "1.0", "risk": "LOW", "score": -1, "model_version": "x"})


def test_state_machine_has_no_direct_fraud_rejection():
    assert "DENIED" not in ALLOWED_TRANSITIONS["PENDING_FRAUD"]
    assert ALLOWED_TRANSITIONS["CLOSED"] == set()


def test_external_dataset_adapter_is_deterministic_and_drops_label():
    path = Path("claims-benchmark/dataset_adapters/mobeen_fatimaa.py")
    spec = importlib.util.spec_from_file_location("dataset_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    row = {"claim_id": "CLM-0000001", "policy_id": "POL-123", "incident_date": "2025-01-02", "incident_type": "Theft", "claim_amount": "123.456", "fraudulent": "Yes"}
    first = module.map_row(row, patient_id=10, plan_id=20, anchor_date=date(2026, 10, 19))
    second = module.map_row(row, patient_id=10, plan_id=20, anchor_date=date(2026, 10, 19))
    assert first == second
    assert "fraudulent" not in first[0]
    assert first[0]["lines"][0]["amount"] == "123.46"
