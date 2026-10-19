from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_database_connection() -> None:
    """Fail startup with a clear error when PostgreSQL is unavailable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

def get_db() -> Session:
    db = SessionLocal()
    try: yield db
    finally: db.close()
