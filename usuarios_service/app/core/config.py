from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    MONGO_CONNECTION_STRING: str
    ALLOWED_ORIGINS: List[str]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()