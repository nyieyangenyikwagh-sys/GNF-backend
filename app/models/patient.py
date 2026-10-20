from datetime import date
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
class Patient(Base, TimestampMixin):
    __tablename__="patients"
    id: Mapped[int]=mapped_column(primary_key=True); owner_user_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"), index=True); first_name: Mapped[str]; last_name: Mapped[str]; dob: Mapped[date]; gender: Mapped[str]
    province: Mapped[str]=mapped_column(default="AB"); phone: Mapped[str|None]; email: Mapped[str|None]; address_line1: Mapped[str|None]; city: Mapped[str|None]; postal_code: Mapped[str|None]
    insurances: Mapped[list["PatientInsurance"]]=relationship(back_populates="patient",cascade="all, delete-orphan")
