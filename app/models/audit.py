from datetime import datetime
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
class AuditLog(Base):
    __tablename__="audit_logs"
    id: Mapped[int]=mapped_column(primary_key=True)
    user_id: Mapped[int|None]=mapped_column(ForeignKey("users.id"))
    claim_id: Mapped[int|None]=mapped_column(ForeignKey("claims.id"), index=True)
    action: Mapped[str]
    resource: Mapped[str]
    correlation_id: Mapped[str]
    claim_version: Mapped[int|None]
    details: Mapped[dict|None]=mapped_column(JSON)
    ip_address: Mapped[str|None]
    created_at: Mapped[datetime]=mapped_column(default=datetime.utcnow)
