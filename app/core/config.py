from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str | None = None
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "gnf-claims"
    JWT_AUDIENCE: str = "gnf-api"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ENVIRONMENT: str = "development"
    RULES_ENGINE_URL: str | None = None
    FRAUD_ENGINE_URL: str | None = None
    SERVICE_TOKEN: str | None = None
    DEPENDENCY_TIMEOUT_SECONDS: float = 2.0
    DEPENDENCY_MAX_RETRIES: int = 2
    RECOVERY_INTERVAL_SECONDS: int = 30
    RECOVERY_MAX_ATTEMPTS: int = 10
    MAX_REQUEST_BYTES: int = 1_048_576
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("DATABASE_URL")
    @classmethod
    def require_postgresql(cls, value: str) -> str:
        if not value.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("DATABASE_URL must use a PostgreSQL connection URL")
        return value

settings = Settings()
