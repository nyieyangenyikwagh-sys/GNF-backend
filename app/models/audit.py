from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
class AuditLog(Base):
    __tablename__="audit_logs"; id: Mapped[int]=mapped_column(primary_key=True); user_id: Mapped[int|None]; action: Mapped[str]; resource: Mapped[str]; ip_address: Mapped[str|None]; created_at: Mapped[datetime]=mapped_column(default=datetime.utcnow)
