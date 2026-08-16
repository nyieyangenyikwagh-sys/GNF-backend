from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base
class ProvincialRule(Base):
    __tablename__="provincial_rules"; id: Mapped[int]=mapped_column(primary_key=True); province: Mapped[str]=mapped_column(index=True); config: Mapped[dict]=mapped_column(JSON)
