from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ClaimStatus = Literal[
    "PENDING_RULES", "PENDING_FRAUD", "FAILED_ASSESSMENT", "REVIEW",
    "HUMAN_REVIEW", "SUBMITTED", "APPROVED", "DENIED", "PAID", "CLOSED",
]


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, protected_namespaces=())


class ClaimLineIn(StrictRequest):
    service_code: str = Field(min_length=1, max_length=32)
    diagnosis_code: str = Field(min_length=1, max_length=32)
    units: int = Field(default=1, ge=1, le=100)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class ClaimCreate(StrictRequest):
    patient_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)
    province: str = Field(default="AB", min_length=2, max_length=2)
    provider_billing_number: str = Field(min_length=1, max_length=32)
    service_date: date
    lines: list[ClaimLineIn] = Field(min_length=1, max_length=100)

    @field_validator("province")
    @classmethod
    def normalize_province(cls, value: str) -> str:
        return value.upper()


class ClaimLineOut(BaseModel):
    service_code: str
    diagnosis_code: str
    units: int
    amount: Decimal
    model_config = ConfigDict(from_attributes=True)


class ClaimOut(BaseModel):
    id: int
    status: ClaimStatus
    province: str
    service_date: date
    billed_amount: Decimal
    denial_reason_code: str | None
    version: int
    lines: list[ClaimLineOut]
    model_config = ConfigDict(from_attributes=True)


class ClaimUpdate(StrictRequest):
    provider_billing_number: str | None = Field(default=None, min_length=1, max_length=32)
    service_date: date | None = None
    lines: list[ClaimLineIn] | None = Field(default=None, min_length=1, max_length=100)


class StatusChange(StrictRequest):
    to_status: ClaimStatus
    reason_code: str | None = Field(default=None, max_length=64)


class AuditEventOut(BaseModel):
    action: str
    correlation_id: str
    claim_version: int | None
    details: dict | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RulesDecision(StrictRequest):
    schema_version: Literal["1.0"]
    outcome: Literal["PASS", "FAIL"]
    reason_codes: list[str] = Field(default_factory=list, max_length=100)
    rules_version: str = Field(min_length=1, max_length=64)


class FraudDecision(StrictRequest):
    schema_version: Literal["1.0"]
    risk: Literal["LOW", "MEDIUM", "HIGH"]
    score: float = Field(ge=0, le=1)
    model_version: str = Field(min_length=1, max_length=64)
