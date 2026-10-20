from datetime import date, datetime, timezone

import pytest
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_current_user
from app.api.v1 import claims
from app.core.database import get_db
from app.core.errors import http_error_handler, validation_error_handler
from app.models import Base
from app.models.insurance import InsurancePlan, PatientInsurance
from app.models.patient import Patient
from app.models.user import User


@pytest.fixture
def api():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    db = session_factory()
    users = {
        name: User(email=f"{name}@test", hashed_password="!", role=role)
        for name, role in {"owner": "claimant", "other": "claimant", "adjuster": "adjuster", "auditor": "auditor"}.items()
    }
    db.add_all(users.values())
    db.flush()
    plan = InsurancePlan(payer_id="AHCIP", name="AHCIP", layer="public", plan_type="public")
    patient = Patient(owner_user_id=users["owner"].id, first_name="Synthetic", last_name="Owner", dob=date(1990, 1, 1), gender="other", province="AB")
    db.add_all([plan, patient])
    db.flush()
    db.add(PatientInsurance(
        patient_id=patient.id, plan_id=plan.id, member_id="MEM-1", health_card_number="123456789",
        effective_date=date(2024, 1, 1), priority="primary", last_verified_at=datetime.now(timezone.utc),
        last_eligibility={"eligible": True},
    ))
    db.commit()

    app = FastAPI()
    app.include_router(claims.router, prefix="/api/v1")
    app.add_exception_handler(HTTPException, http_error_handler)
    from fastapi.exceptions import RequestValidationError
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    def db_override():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def user_override(x_test_user: str = Header(default="owner")):
        session = session_factory()
        try:
            return session.query(User).filter(User.email == f"{x_test_user}@test").one()
        finally:
            session.close()

    app.dependency_overrides[get_db] = db_override
    app.dependency_overrides[get_current_user] = user_override
    client = TestClient(app)
    yield client, {"patient_id": patient.id, "plan_id": plan.id}
    db.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


def payload(reference):
    return {
        **reference, "province": "AB", "provider_billing_number": "123456",
        "service_date": date.today().isoformat(),
        "lines": [{"service_code": "03.03A", "diagnosis_code": "J06.9", "units": 1, "amount": "85.00"}],
    }


def test_idempotent_creation_and_owner_isolation(api):
    client, reference = api
    headers = {"Idempotency-Key": "test-key-0001"}
    first = client.post("/api/v1/claims", json=payload(reference), headers=headers)
    second = client.post("/api/v1/claims", json=payload(reference), headers=headers)
    assert first.status_code == 201, first.text
    assert first.json()["status"] == "SUBMITTED"
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert client.get(f"/api/v1/claims/{first.json()['id']}", headers={"X-Test-User": "other"}).status_code == 404
    assert client.get("/api/v1/claims", headers={"X-Test-User": "other"}).json() == []


def test_mass_assignment_does_not_create_partial_record(api):
    client, reference = api
    body = payload(reference)
    body["status"] = "APPROVED"
    response = client.post("/api/v1/claims", json=body, headers={"Idempotency-Key": "test-key-0002"})
    assert response.status_code == 422
    assert client.get("/api/v1/claims").json() == []


def test_auditor_cannot_change_status(api):
    client, reference = api
    created = client.post("/api/v1/claims", json=payload(reference), headers={"Idempotency-Key": "test-key-0003"}).json()
    response = client.post(f"/api/v1/claims/{created['id']}/status", json={"to_status": "APPROVED"}, headers={"X-Test-User": "auditor"})
    assert response.status_code == 403
