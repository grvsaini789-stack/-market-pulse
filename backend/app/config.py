from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    twitter_bearer_token: str = ""  # optional, for Twitter/X source

    database_url: str = "sqlite+aiosqlite:///./market_pulse.db"
    cors_origins: str = '["http://localhost:3000"]'
    pipeline_interval_minutes: int = 10
    news_lookback_days: int = 14

    @property
    def cors_origins_list(self) -> List[str]:
        try:
            return json.loads(self.cors_origins)
        except Exception:
            return ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
