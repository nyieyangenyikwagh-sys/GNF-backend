from datetime import date, datetime
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
class InsurancePlan(Base, TimestampMixin):
    __tablename__="insurance_plans"; id: Mapped[int]=mapped_column(primary_key=True); payer_id: Mapped[str]=mapped_column(unique=True,index=True); name: Mapped[str]; layer: Mapped[str]; plan_type: Mapped[str|None]
class PatientInsurance(Base, TimestampMixin):
    __tablename__="patient_insurances"; id: Mapped[int]=mapped_column(primary_key=True); patient_id: Mapped[int]=mapped_column(ForeignKey("patients.id")); plan_id: Mapped[int]=mapped_column(ForeignKey("insurance_plans.id")); member_id: Mapped[str]; health_card_number: Mapped[str|None]; group_number: Mapped[str|None]; effective_date: Mapped[date]; termination_date: Mapped[date|None]; priority: Mapped[str]=mapped_column(default="primary"); last_verified_at: Mapped[datetime|None]; last_eligibility: Mapped[dict|None]=mapped_column(JSON); patient: Mapped["Patient"]=relationship(back_populates="insurances")
