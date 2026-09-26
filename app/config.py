from pathlib import Path
from pydantic import SecretStr

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # points to backend/


class Settings(BaseSettings):
    github_token: SecretStr
    github_api_url: str = "https://api.github.com"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
