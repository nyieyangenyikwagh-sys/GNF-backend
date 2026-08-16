from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin
class Appeal(Base, TimestampMixin):
    __tablename__="appeals"; id: Mapped[int]=mapped_column(primary_key=True); claim_id: Mapped[int]=mapped_column(ForeignKey("claims.id")); denial_reason_code: Mapped[str]; note: Mapped[str|None]; supporting_doc_url: Mapped[str|None]; outcome: Mapped[str]=mapped_column(default="pending"); resolved_at: Mapped[datetime|None]
