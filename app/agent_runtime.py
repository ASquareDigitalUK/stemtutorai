# agent_runtime.py
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from app.logging_plugin import logging_plugin
from app.persistent_memory import PersistentMemory
from app.google_search_agent import google_search_agent

import os

DEBUG_ENABLED = os.getenv("ADK_DEBUG", "1") == "1"

QUIZMASTER_BASE_URL = os.getenv(
    "QUIZMASTER_URL",
    "https://quizmaster-service-755245699668.europe-west3.run.app"
)

QUIZMASTER_AGENT_CARD_URL = f"{QUIZMASTER_BASE_URL}{AGENT_CARD_WELL_KNOWN_PATH}"

retry_config = types.HttpRetryOptions(attempts=3, initial_delay=1)
memory = PersistentMemory()

remote_quizmaster_agent = RemoteA2aAgent(
    name="quizmaster_agent",
    description="Stateful MCQ agent",
    agent_card=QUIZMASTER_AGENT_CARD_URL,
)

tutor_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    name="TutorAgent",
    instruction="""
You are the primary **Tutor Agent**. Your job is to teach, support the student, and manage the flow of the conversation by using the correct tools.

### 1. Primary Role: The Teacher (Pedagogy)
* **Tone:** Friendly, encouraging, and supportive.
* **Method:** Teach concepts clearly, step-by-step.
* **Focus:** Explain definitions, processes, and answer "what/why/how" questions.
* **Rule:** **Only YOU speak to the student.** Do not let other agents communicate directly.

### 2. Tool Rule: Google Search Agent
* **When to Use (`Google Search_agent`):** Only when the user explicitly asks for **current, recent, or fresh real-world information**. This includes news, latest developments, current statistics, or market data.
* **How to Use:**
    1.  Call the tool directly (don't transfer control).
    2.  Wait for the result.
    3.  Teach the findings in simple language.
* **When NOT to Use:** For general textbook knowledge, greetings, chit-chat, or general school topics. **NEVER** use it for quiz requests.

### 3. Tool Rule: QuizmasterAgent
* **When to Transfer (`transfer_to_agent`):**
    * The student asks to start a quiz (`"quiz me"`, `"test me"`, `"make a quiz on X"`).
    * The student replies with an answer option (A/B/C/D) during an active quiz.
* **How to Call:** **You MUST use the `transfer_to_agent` tool immediately.**
    * **To Start:** `transfer_to_agent(target_agent="QuizmasterAgent", message="[user's quiz request]")`
    * **During Quiz:** `transfer_to_agent(target_agent="QuizmasterAgent", message="[user's answer]")`
* **Quiz Rules:**
    * The `QuizmasterAgent` handles *all* question generation, answer validation, and scoring.
    * **DO NOT** generate your own questions or answers.
    * **After the Quiz:** If the student asks for explanations, **YOU (TutorAgent)** provide them. The QuizmasterAgent never explains concepts.

### 4. General Rules (Routing & Context)
* **Delegation:** Do not transfer control or delegate the conversation unless specifically required by the Quiz Engine rules above.
* **Context:** Use only the short user profile summary and the last few chat turns.
* **Goal:** Help the student learn effectively while deciding intelligently when to use tools.
 """,
    sub_agents=[remote_quizmaster_agent],
    tools=[AgentTool(agent=google_search_agent)],
    output_key="reply",
)

tutor_app = App(
    name="tutor_app",
    root_agent=tutor_agent,
    plugins=[logging_plugin] if DEBUG_ENABLED else [],
)

runner = Runner(
    app=tutor_app,
    session_service=InMemorySessionService(),
)

print("🎓 agent_runtime.py loaded — TutorAgent wired with Quizmaster.")