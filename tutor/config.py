import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class TutorSettings(BaseSettings):
    # Google APIs
    GOOGLE_API_KEY: str
    CSE_API_KEY: str
    CSE_ID: str

    # URLs
    QUIZMASTER_URL: str = "https://quizmaster-service-hrzbcuuvla-ew.a.run.app"
    TUTOR_URL: str | None = None

    # Ports (local dev only)
    TUTOR_PORT: int = 7070

    # Models
    TUTOR_MODEL: str
    SUBJECT_CLASSIFIER_MODEL: str
    INTENT_CLASSIFIER_MODEL: str

    # Firestore (optional)
    FIRESTORE_CREDENTIALS_JSON_PATH: str | None = None

    # Memory + Retry
    MEMORY_DIR: str = "/tmp/tutor_memory"
    RETRY_ATTEMPTS: int = 3
    RETRY_INITIAL_DELAY: float = 0.5

    # Classifier compaction
    SUBJECT_CLASSIFIER_COMPACTION_INTERVAL: int = 5
    SUBJECT_CLASSIFIER_OVERLAP_SIZE: int = 1
    INTENT_CLASSIFIER_COMPACTION_INTERVAL: int = 5
    INTENT_CLASSIFIER_OVERLAP_SIZE: int = 1

    # Debug
    ADK_DEBUG: int = 1

    class Config:
        #env_file = ".env.prod"
        extra = "ignore"


settings = TutorSettings()
