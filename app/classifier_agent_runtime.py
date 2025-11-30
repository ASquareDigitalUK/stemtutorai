from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.apps import App
from google.adk.runners import Runner, InMemorySessionService
from app.logging_plugin import logging_plugin

# ----------------------------
# CLASSIFIER AGENT
# ----------------------------
classifier_agent = Agent(
    name="SubjectClassifier",
    model=Gemini(model="gemini-2.5-flash"),
    instruction="""
You are a Subject Classification Agent.

Your job is to read a student's question and classify it into:
1. The school subject (e.g. Math, Science, Physics, Chemistry…)
2. The topic (e.g. Algebra, Photosynthesis, Electricity…)
3. A confidence score 0–1.

Keep the topic broad and general — NOT overly specific.

You MUST output ONLY a valid JSON object. Do NOT wrap the JSON in backticks.
""",
    output_key="classification"
)

# Wrap in an App + Runner
classifier_app = App(
    name="classifier_app",
    root_agent=classifier_agent,
    plugins=[logging_plugin],  #Add the plugin. Handles standard Observability logging across ALL agents
)

classifier_runner = Runner(
    app=classifier_app,
    session_service=InMemorySessionService()
)

print("📘 SubjectClassifier Agent & Runner initialized and saved.")