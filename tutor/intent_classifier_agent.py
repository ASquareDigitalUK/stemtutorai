from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.apps import App
from google.adk.runners import Runner, InMemorySessionService
from google.adk.apps.app import EventsCompactionConfig

from tutor.logging_plugin import logging_plugin
from tutor.config import settings

# ----------------------------
# INTENT CLASSIFIER AGENT
# ----------------------------
intent_classifier_agent = Agent(
    name="IntentClassifierAgent",
    model=Gemini(model=settings.INTENT_CLASSIFIER_MODEL),
    instruction="""
You are an Intent Classification Agent.

Given a user's message, classify it into ONE of the following intents:

1. "greeting"
   - hi, hello, hey, good morning, good evening, thanks, bye, etc.

2. "small_talk"
   - casual or social conversation not related to learning or quizzes
     (e.g. "how is your day?", "what's up?", "you are cool")

3. "quiz_answer"
   - single-letter responses like "A", "B", "C", "D"
   - or short numeric answers like "7", "12", including simple variants:
       "I think it's B", "maybe C?"

4. "request_quiz"
   - user explicitly indicates they want to start a quiz:
       "test me", "give me a quiz", "practice questions", "start MCQs"

5. "academic_question"
   - any learning, subject-related, or topic-related question:
       "explain gravity", "help me understand algebra",
       "what is photosynthesis?"

6. "off_topic"
   - anything that does not fall into the above categories

----------------------
Output strictly valid JSON (do not wrap in backticks):

{
  "intent": "string",
  "confidence": 0.0
}

The confidence score is between 0 and 1.
""",
    output_key="intent_data"
)

# ----------------------------
# APP
# ----------------------------
intent_classifier_app = App(
    name="intent_classifier_app",
    root_agent=intent_classifier_agent,
    plugins=[logging_plugin] if settings.ADK_DEBUG else [],
    #events_compaction_config=EventsCompactionConfig(
    #    compaction_interval=settings.INTENT_CLASSIFIER_COMPACTION_INTERVAL,
    #    overlap_size=settings.INTENT_CLASSIFIER_OVERLAP_SIZE,
    #),
)


# ----------------------------
# RUNNER
# ----------------------------
intent_classifier_runner = Runner(
    app=intent_classifier_app,
    session_service=InMemorySessionService(),
)

print("🧭 IntentClassifierAgent initialized successfully.")