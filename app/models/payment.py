from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin
class Payment(Base, TimestampMixin):
    __tablename__="payments"; id: Mapped[int]=mapped_column(primary_key=True); claim_id: Mapped[int]=mapped_column(ForeignKey("claims.id")); era_number: Mapped[str]; eob_reference: Mapped[str|None]; paid_amount: Mapped[float]=mapped_column(Numeric(10,2)); underpaid: Mapped[bool]=mapped_column(default=False); remittance: Mapped[str|None]
