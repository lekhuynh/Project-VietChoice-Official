from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    redis_url: str = "redis://redis:6379/0"
    queues: list[str] = ["crawl", "auto_update"]


settings = Settings()
