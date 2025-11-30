# quizmaster_server.py
"""
Quizmaster Service
------------------
This module exposes the QuizmasterAgent as an A2A agent using the ADK adapter.
fastapi_server.py mounts this under /quizmaster.

All logic, tools, state, question loading remain unchanged.
"""

import os
import json
import logging
import requests
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.routing import Route

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.genai import types
from google import genai

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_genai_client = genai.Client()
retry_config = types.HttpRetryOptions(attempts=3, initial_delay=1)


@dataclass
class QuizState:
    active: bool = False
    topic: Optional[str] = None
    difficulty: str = "easy"
    total_questions: int = 5
    current_index: int = 0
    current_correct_option: Optional[str] = None
    score: int = 0
    questions_list: List[Dict[str, Any]] = field(default_factory=list)


quiz_state = QuizState()

QUESTION_DATA_URL_KEY = "QUIZ_DATA_GITHUB_URL"
DEFAULT_QUESTION_URL = (
    "https://raw.githubusercontent.com/vishukulkarni/Questions/main/questions_enriched.json"
)


def _load_static_questions():
    try:
        res = requests.get(os.getenv(QUESTION_DATA_URL_KEY, DEFAULT_QUESTION_URL), timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.error(f"❌ Failed to load quiz data: {e}")
        return []


ALL_STATIC_QUESTIONS = _load_static_questions()


# ---------- TOOLS (UNCHANGED) ----------
def web_search(topic: str, max_snippets: int = 3) -> str:
    api_key = os.getenv("GOOGLE_CSE_API_KEY")
    cse_id = os.getenv("GOOGLE_CSE_ID")
    if not api_key or not cse_id:
        return f"(Search disabled — general knowledge only for '{topic}')."
    try:
        url = (
            "https://www.googleapis.com/customsearch/v1"
            f"?key={api_key}&cx={cse_id}&q={topic}"
        )
        res = requests.get(url, timeout=8)
        res.raise_for_status()
        items = res.json().get("items", [])
        snippets = [item.get("snippet") for item in items[:max_snippets] if item.get("snippet")]
        return "\n".join(snippets) or f"(No search snippets available.)"
    except Exception as e:
        return f"(Search error: {e})"


def _format_mcq(index, qdata):
    opts = qdata["options"]
    return (
        f"Question {index}: {qdata['question']}\n"
        f"A) {opts['A']}\n"
        f"B) {opts['B']}\n"
        f"C) {opts['C']}\n"
        f"D) {opts['D']}"
    )


def _normalize_question(raw_q):
    raw_opts = [str(x) for x in raw_q.get("options", [])[:4]]
    options = {chr(65 + i): val for i, val in enumerate(raw_opts)}
    correct = raw_q.get("answer")
    if isinstance(correct, str) and correct.strip().upper() in "ABCD":
        return {"question": raw_q["question"], "options": options, "correct_option": correct}
    return {"question": raw_q["question"], "options": options, "correct_option": None}


def _get_available_data(questions):
    subjects = {q.get("subject", "").lower() for q in questions if q.get("subject")}
    topics = {q.get("topic", "").lower() for q in questions if q.get("topic")}
    return {"subjects": subjects, "topics": topics}


def start_quiz(topic: str, difficulty: str = "easy", num_questions: int = 5) -> str:
    # UNCHANGED LOGIC
    # ...
    return "..."


def answer_question(user_answer: str) -> str:
    # UNCHANGED LOGIC
    return "..."


# ---------- QUIZMASTER AGENT ----------
quizmaster_agent = LlmAgent(
    model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
    name="QuizmasterAgent",
    description="Stateful MCQ quiz engine with Google Search grounding.",
    instruction="Use tools. Never speak directly.",
    tools=[web_search, start_quiz, answer_question],
)

# ---------- A2A SERVER ----------
QUIZMASTER_PORT = int(os.getenv("PORT", "8080"))

quizmaster_a2a_app = to_a2a(
    quizmaster_agent,
    port=QUIZMASTER_PORT,
)

# EXPOSE AGENT CARD
#AGENT_CARD = quizmaster_agent.export_card()

#@quizmaster_a2a_app.get("/.well-known/agent.json")
#def agent_json():
#    # NOTE: ADK stores the export card on the A2A wrapper, not on LlmAgent
#    return JSONResponse(content=quizmaster_a2a_app.agent_card)

# EXTRA ROUTE
def quiz_state_endpoint(request):
    return JSONResponse({"active": quiz_state.active})


quizmaster_a2a_app.router.routes.append(
    Route("/quiz_state", endpoint=quiz_state_endpoint, methods=["GET"])
)

print(f"✅ Quizmaster A2A app ready on port {QUIZMASTER_PORT}")