from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base, TimestampMixin
class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str]
    role: Mapped[str] = mapped_column(default="biller")
    is_active: Mapped[bool] = mapped_column(default=True)
