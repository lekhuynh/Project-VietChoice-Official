from pathlib import Path
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict

# Point to be/.env
BASE_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # ignore unrelated keys present in .env
    )

    # SQL Server credentials
    db_driver: str
    db_server: str
    db_name: str
    db_user: str
    db_password: str

    # Auth configuration
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    ACCESS_TOKEN_COOKIE_NAME: str

    # External services
    GEMINI_API_KEY: str | None = None

    @property
    def SQLSERVER_URL(self) -> str:
        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        driver = quote_plus(self.db_driver)
        return (
            f"mssql+pyodbc://{user}:{password}@{self.db_server}/{self.db_name}"
            f"?driver={driver}"
            f"&TrustServerCertificate=yes"
            f"&charset=utf8"
        )


settings = Settings()
