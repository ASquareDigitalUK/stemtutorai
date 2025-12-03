import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class QuizmasterSettings(BaseSettings):
    # Google APIs
    GOOGLE_API_KEY: str
    CSE_API_KEY: str
    CSE_ID: str

    # Question dataset
    QUESTION_DATA_URL: str
    QUIZMASTER_URL: str
    QUIZMASTER_PORT: int = 8080
    TEST_TOKEN: str

    # Models
    QUIZMASTER_MODEL: str

    # Retry
    RETRY_ATTEMPTS: int = 3
    RETRY_INITIAL_DELAY: float = 0.5

    # Debug
    ADK_DEBUG: int = 1

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = QuizmasterSettings()