import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class UISettings(BaseSettings):
    # URLs
    TUTOR_URL: str
    UI_URL: str | None = None  # optional, Cloud Run doesn't provide it

    # Ports (for local dev only)
    UI_PORT: int = 7860

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = UISettings()