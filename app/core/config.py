"""Pydantic settings for application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database settings
    POSTGRES_USER: str = "cinematch"
    POSTGRES_PASSWORD: str = "cinematch123"
    POSTGRES_DB: str = "cinematch"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "6432"

    # JWT settings
    SECRET_KEY: str = "supersecretkeyforjwtdev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    @property
    def database_url(self) -> str:
        """Build database URL from components."""
        return ( f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
