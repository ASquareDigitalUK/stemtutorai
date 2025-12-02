import os
import json
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load local .env in development (ignored safely in Cloud Run)
load_dotenv()

class Settings(BaseSettings):
    """Strict configuration loader for production.

    All environment variables are REQUIRED.
    Missing variables will cause the application to fail fast.
    """

    # Required environment vars
    GOOGLE_API_KEY: str
    CSE_API_KEY: str
    CSE_ID: str

    QUESTION_DATA_URL: str
    QUIZMASTER_URL: str
    TUTOR_URL: str
    UI_URL: str

    QUIZMASTER_PORT: int
    TUTOR_PORT: int
    UI_PORT: int

    TEST_TOKEN: str

    TUTOR_MODEL: str
    QUIZMASTER_MODEL: str
    SUBJECT_CLASSIFIER_MODEL: str
    INTENT_CLASSIFIER_MODEL: str

    # Optional Firestore credentials JSON
    FIRESTORE_CREDENTIALS_JSON_PATH: str | None = None

    # Compaction Settings
    SUBJECT_CLASSIFIER_COMPACTION_INTERVAL: int
    SUBJECT_CLASSIFIER_OVERLAP_SIZE: int
    INTENT_CLASSIFIER_COMPACTION_INTERVAL: int
    INTENT_CLASSIFIER_OVERLAP_SIZE: int

    # Debug flag
    ADK_DEBUG: bool = True
    MEMORY_DIR: str
    RETRY_ATTEMPTS: int
    RETRY_INITIAL_DELAY: float

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()