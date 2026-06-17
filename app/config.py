from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://sentiment:sentiment@localhost:5432/sentimenttrend"
    webhook_url: str = ""
    alert_negative_threshold: int = 3
    alert_window_minutes: int = 60
    alert_score_threshold: float = -0.3
    auto_seed_demo: bool = True
    seed_demo_reset: bool = False


settings = Settings()
