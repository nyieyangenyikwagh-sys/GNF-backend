from datetime import date, datetime
from sqlalchemy import ForeignKey, JSON, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
class Claim(Base, TimestampMixin):
    __tablename__="claims"; id: Mapped[int]=mapped_column(primary_key=True); patient_id: Mapped[int]=mapped_column(ForeignKey("patients.id")); plan_id: Mapped[int]=mapped_column(ForeignKey("insurance_plans.id")); province: Mapped[str]=mapped_column(default="AB"); provider_billing_number: Mapped[str]; service_date: Mapped[date]; status: Mapped[str]=mapped_column(default="draft"); billed_amount: Mapped[float]=mapped_column(Numeric(10,2),default=0); denial_reason_code: Mapped[str|None]; coverage_snapshot: Mapped[dict|None]=mapped_column(JSON)
    lines: Mapped[list["ClaimLine"]]=relationship(back_populates="claim",cascade="all, delete-orphan"); history: Mapped[list["ClaimStatusHistory"]]=relationship(back_populates="claim",cascade="all, delete-orphan")
class ClaimLine(Base):
    __tablename__="claim_lines"; id: Mapped[int]=mapped_column(primary_key=True); claim_id: Mapped[int]=mapped_column(ForeignKey("claims.id")); service_code: Mapped[str]; diagnosis_code: Mapped[str]; units: Mapped[int]=mapped_column(default=1); amount: Mapped[float]=mapped_column(Numeric(10,2),default=0); claim: Mapped["Claim"]=relationship(back_populates="lines")
class ClaimStatusHistory(Base):
    __tablename__="claim_status_history"; id: Mapped[int]=mapped_column(primary_key=True); claim_id: Mapped[int]=mapped_column(ForeignKey("claims.id")); from_status: Mapped[str|None]; to_status: Mapped[str]; reason_code: Mapped[str|None]; created_at: Mapped[datetime]=mapped_column(default=datetime.utcnow); claim: Mapped["Claim"]=relationship(back_populates="history")
