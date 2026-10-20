from datetime import date, datetime
from sqlalchemy import ForeignKey, JSON, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
class Claim(Base, TimestampMixin):
    __tablename__="claims"
    __table_args__=(UniqueConstraint("owner_user_id", "idempotency_key", name="uq_claim_owner_idempotency"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    patient_id: Mapped[int]=mapped_column(ForeignKey("patients.id"))
    plan_id: Mapped[int]=mapped_column(ForeignKey("insurance_plans.id"))
    owner_user_id: Mapped[int]=mapped_column(ForeignKey("users.id"), index=True)
    idempotency_key: Mapped[str]=mapped_column(String(128))
    request_hash: Mapped[str]=mapped_column(String(64))
    correlation_id: Mapped[str]=mapped_column(String(128))
    version: Mapped[int]=mapped_column(default=1)
    province: Mapped[str]=mapped_column(default="AB")
    provider_billing_number: Mapped[str]
    service_date: Mapped[date]
    status: Mapped[str]=mapped_column(default="PENDING_RULES")
    billed_amount: Mapped[float]=mapped_column(Numeric(12,2),default=0)
    denial_reason_code: Mapped[str|None]
    coverage_snapshot: Mapped[dict|None]=mapped_column(JSON)
    rules_result: Mapped[dict|None]=mapped_column(JSON)
    fraud_result: Mapped[dict|None]=mapped_column(JSON)
    assessment_claim_version: Mapped[int|None]
    assessment_attempts: Mapped[int]=mapped_column(default=0)
    next_retry_at: Mapped[datetime|None]
    lines: Mapped[list["ClaimLine"]]=relationship(back_populates="claim",cascade="all, delete-orphan"); history: Mapped[list["ClaimStatusHistory"]]=relationship(back_populates="claim",cascade="all, delete-orphan")
class ClaimLine(Base):
    __tablename__="claim_lines"; id: Mapped[int]=mapped_column(primary_key=True); claim_id: Mapped[int]=mapped_column(ForeignKey("claims.id")); service_code: Mapped[str]; diagnosis_code: Mapped[str]; units: Mapped[int]=mapped_column(default=1); amount: Mapped[float]=mapped_column(Numeric(10,2),default=0); claim: Mapped["Claim"]=relationship(back_populates="lines")
class ClaimStatusHistory(Base):
    __tablename__="claim_status_history"; id: Mapped[int]=mapped_column(primary_key=True); claim_id: Mapped[int]=mapped_column(ForeignKey("claims.id")); from_status: Mapped[str|None]; to_status: Mapped[str]; reason_code: Mapped[str|None]; actor_user_id: Mapped[int|None]; correlation_id: Mapped[str]; claim_version: Mapped[int]; created_at: Mapped[datetime]=mapped_column(default=datetime.utcnow); claim: Mapped["Claim"]=relationship(back_populates="history")
