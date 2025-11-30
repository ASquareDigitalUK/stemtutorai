import random
from typing import Optional, List

# -------------------------------------------------------------------
# MOCK QUIZ STATE
# Note: The true active state is checked against the remote server
# or memory, but this function needs a placeholder for orchestration.
# -------------------------------------------------------------------
# Since this local file is only used to satisfy imports and provide
# mock subject data, we keep the quiz active state simple.
def is_quiz_active() -> bool:
    """MOCK: Checks if a quiz is currently running."""
    # The actual check that matters is inside the orchestrator using a more reliable source
    return False

# -------------------------------------------------------------------
# MOCK SUBJECT/TOPIC DATA (Required for orchestrator's Case 1 logic)
# -------------------------------------------------------------------

SUPPORTED_SUBJECTS = {
    "math": ["linear equations", "fractions", "probability", "geometry", "calculus", "statistics"],
    "science": ["electromagnetism", "photosynthesis", "cellular respiration", "Newton's laws", "chemical bonding"]
}

def get_supported_subjects() -> List[str]:
    """Returns a list of supported subject keys."""
    return list(SUPPORTED_SUBJECTS.keys())

def get_topic_examples(subject: str) -> List[str]:
    """Returns a list of example topics for a given subject."""
    return SUPPORTED_SUBJECTS.get(subject.lower(), [])

print("📚 quizmaster_tool.py loaded with mock quiz functions.")