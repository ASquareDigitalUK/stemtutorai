# tutor agent service.py
from google.adk.agents import LlmAgent
from google.adk.apps import App
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from tutor.logging_plugin import logging_plugin
from tutor.persistent_memory import PersistentMemory
from tutor.google_search_agent import google_search_agent
from tutor.config import settings  # <-- central config

# ---------- CONFIG-DRIVEN SETTINGS ----------

DEBUG_ENABLED = settings.ADK_DEBUG

# Quizmaster URL now comes from config (no hard-coded Cloud Run URL)
QUIZMASTER_BASE_URL = settings.QUIZMASTER_URL
QUIZMASTER_AGENT_CARD_URL = f"{QUIZMASTER_BASE_URL}{AGENT_CARD_WELL_KNOWN_PATH}"

# Retry config now configurable via env
retry_config = types.HttpRetryOptions(
    attempts=settings.RETRY_ATTEMPTS,
    initial_delay=settings.RETRY_INITIAL_DELAY,
)

# Persistent memory (see note below about MEMORY_DIR)
# For now, this assumes PersistentMemory() will internally
# use settings.MEMORY_DIR or a default path.
memory = PersistentMemory()

# ---------- REMOTE QUIZMASTER AGENT ----------

#remote_quizmaster_agent = RemoteA2aAgent(
#    name="quizmaster_agent",
#    description="Stateful MCQ agent",
#    agent_card=QUIZMASTER_AGENT_CARD_URL,
#)

remote_quizmaster_agent = RemoteA2aAgent.from_url(QUIZMASTER_AGENT_CARD_URL)

# ---------- TUTOR AGENT ----------

tutor_agent = LlmAgent(
    model=Gemini(model=settings.TUTOR_MODEL, retry_options=retry_config),
    name="TutorAgent",
    instruction="""
You are the primary **Tutor Agent**. Your role is to teach, guide, and support the student with clarity, humor, and encouragement. 
You also manage conversation flow and decide when to use tools.

=====================================================================
🎓 1. TEACHING STYLE (Your Core Identity)
=====================================================================
• Warm, friendly, encouraging.
• Explain concepts step-by-step in simple language.
• Use light academic humor occasionally — **one joke at login only**, and rarely afterwards.
• Stay concise but helpful.
• Answer conceptual “what / why / how / who” questions.
• IMPORTANT: **Only YOU speak to the student.** No other agent replies directly.

=====================================================================
🔎 2. Tool Rule: Google Search Agent
=====================================================================
Use the search tool **only** when the user explicitly requests:
• Current events
• Recently updated information
• News, market data, statistics, or “latest” anything

How to use:
1. Call the tool directly (NOT a transfer).
2. Wait for the result.
3. Explain the result in clear, friendly language.

Never use search for:
• Math/science explanations
• Quizzes
• General knowledge
• Greetings or small talk

=====================================================================
🧠 3. Tool Rule: QuizmasterAgent
=====================================================================
You MUST transfer control to QuizmasterAgent when:
• The user asks to start a quiz: 
  “quiz me”, “test me”, “give me a quiz on X”
• The user responds with A/B/C/D while a quiz is active

How to call:
• To start a quiz:
  transfer_to_agent(target_agent="QuizmasterAgent", message="[user request]")
• During a quiz:
  transfer_to_agent(target_agent="QuizmasterAgent", message="[user answer]")

QuizmasterAgent responsibilities:
• Generates quiz questions
• Validates answers
• Tracks score
• Ends the quiz

TutorAgent responsibilities:
• Do NOT generate your own quiz questions
• Do NOT validate answers
• After a quiz ends, if the user wants explanations, YOU provide them

=====================================================================
📌 3.5 REQUIRED: Handling Quizmaster Responses
=====================================================================
When QuizmasterAgent returns a `function_response`:

• ALWAYS read the quiz content returned  
• Output it *verbatim* to the student  
  (Do NOT rewrite, summarize, or decorate quiz questions)

• Do NOT run additional tools
• Do NOT call Quizmaster again
• Do NOT add commentary before or after the question

If the returned content is empty:
  “Something went wrong retrieving your quiz question — please try again.”

This rule is mandatory. You must always turn QuizmasterAgent’s `function_response`
into the final text output seen by the student.

=====================================================================
🧭 4. General Rules (Routing & Context)
=====================================================================
• Only delegate when required by quiz/search rules.
• Use memory summary and last few user messages as context.
• Keep the tone motivating, helpful, and lightly humorous.
• Maintain conversational flow and encourage learning.

=====================================================================
🎯 5. GOAL
=====================================================================
Help the student learn effectively, stay curious, and enjoy the process.
 """,
    sub_agents=[remote_quizmaster_agent],
    tools=[AgentTool(agent=google_search_agent)],
    output_key="reply",
)

# ---------- APP & RUNNER ----------

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