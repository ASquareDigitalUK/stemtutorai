# quizmaster_server.py
"""
Secure, production-ready version of quizmaster_server.py
- Uses config.py for environment variables
- Does NOT load secrets or URLs from code
- Does NOT commit any .env files
"""

import os
import json
import logging
import requests
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from starlette.responses import JSONResponse
from starlette.routing import Route

from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.genai import types
from google import genai

# Load secure settings
from config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_genai_client = genai.Client()
retry_config = types.HttpRetryOptions(attempts=3, initial_delay=1)

# -----------------------------------------------------------
# QUIZ STATE
# -----------------------------------------------------------

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

def _load_static_questions():
    """Loads questions from external URL defined by environment variable."""
    try:
        res = requests.get(settings.QUESTION_DATA_URL, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        logger.error(f"❌ Failed to load quiz data: {e}")
        return []

ALL_STATIC_QUESTIONS = []

# -----------------------------------------------------------
# TOOLS
# -----------------------------------------------------------

def web_search(topic: str, max_snippets: int = 3) -> str:
    api_key = settings.CSE_API_KEY
    cse_id = settings.CSE_ID

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
        return "\n".join(snippets) or "(No search snippets available.)"
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
    global quiz_state

    if not ALL_STATIC_QUESTIONS:
        return "Quiz data is unavailable. Please check the static question source."

    available_data = _get_available_data(ALL_STATIC_QUESTIONS)
    clean_input = topic.lower().strip()

    questions_to_filter = ALL_STATIC_QUESTIONS
    is_subject_only = clean_input in available_data["subjects"]

    if is_subject_only:
        questions_to_filter = [q for q in ALL_STATIC_QUESTIONS if q.get("subject", "").lower() == clean_input]

    search_context = web_search(topic)

    prompt = f"""
    You are a quiz selector agent. Your job is to select the most relevant questions.

    The user wants a quiz on: "{topic}". 
    Select ONLY the most relevant {num_questions} questions.

    Search context:
    --------------------
    {search_context}
    --------------------

    Questions:
    --------------------
    {json.dumps([q for q in questions_to_filter], indent=2)}
    --------------------

    Output ONLY a JSON list of selected questions.
    """

    filtered_questions = []
    try:
        resp = _genai_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
        )
        text = resp.text.strip()
        if text.startswith("```"):
            text = "\n".join(text.split("\n")[1:-1]).strip()

        filtered_questions = json.loads(text)

    except Exception:
        if clean_input and not is_subject_only:
            topic_match_questions = [q for q in ALL_STATIC_QUESTIONS if clean_input in q.get("topic", "").lower()]
            if topic_match_questions:
                filtered_questions = topic_match_questions[:num_questions]
            else:
                suggestions = ", ".join(sorted(available_data["topics"])[:5])
                return (
                    f"I couldn't find any questions for \"{topic.strip()}\". "
                    f"Try one of: {suggestions}."
                )
        elif is_subject_only:
            filtered_questions = questions_to_filter[:num_questions]
        else:
            import random
            filtered_questions = random.sample(ALL_STATIC_QUESTIONS, min(num_questions, len(ALL_STATIC_QUESTIONS)))

    all_normalized_questions = [_normalize_question(q) for q in filtered_questions]
    normalized_questions = [q for q in all_normalized_questions if q["correct_option"]]

    if not normalized_questions:
        return f"No valid questions found for '{topic}'."

    qdata = normalized_questions[0]

    quiz_state = QuizState(
        active=True,
        topic=topic,
        difficulty=difficulty,
        total_questions=len(normalized_questions),
        current_index=1,
        current_correct_option=qdata["correct_option"],
        score=0,
        questions_list=normalized_questions,
    )

    intro = (
        f"Great! Let's start a {difficulty} quiz on **{topic}**.\n"
        "Answer with A, B, C, or D.\n\n"
    )

    return intro + _format_mcq(1, qdata)

def answer_question(user_answer: str) -> str:
    global quiz_state

    if not quiz_state.active:
        return "No active quiz. Ask me to start one!"

    ans = user_answer.strip().upper()
    if ans not in ["A", "B", "C", "D"]:
        return "Please answer with a single letter: A, B, C, or D."

    correct = quiz_state.current_correct_option or "A"

    if ans == correct:
        quiz_state.score += 1
        feedback = f"✅ Correct! Option {correct} was the right answer."
    else:
        feedback = f"❌ Incorrect. The correct answer was **{correct}**."

    if quiz_state.current_index >= quiz_state.total_questions:
        quiz_state.active = False
        return feedback + f"\n\n🎉 Quiz completed! Score: {quiz_state.score}/{quiz_state.total_questions}."

    quiz_state.current_index += 1
    next_question_index = quiz_state.current_index - 1

    qdata = quiz_state.questions_list[next_question_index]
    quiz_state.current_correct_option = qdata["correct_option"]

    return feedback + "\n\n" + _format_mcq(quiz_state.current_index, qdata)

# -----------------------------------------------------------
# QUIZMASTER AGENT
# -----------------------------------------------------------

quizmaster_agent = LlmAgent(
    model=Gemini(model=settings.QUIZMASTER_MODEL, retry_options=retry_config),
    name="QuizmasterAgent",
    description="Stateful MCQ quiz engine with Google Search grounding.",
    instruction="Use tools. Never speak directly.",
    tools=[web_search, start_quiz, answer_question],
)

QUIZMASTER_PORT = settings.QUIZMASTER_PORT

quizmaster_a2a_app = to_a2a(quizmaster_agent, port=QUIZMASTER_PORT)

# -----------------------------------------------------------
# EXTRA ROUTES (STARLETTE STYLE)
# -----------------------------------------------------------

TEST_TOKEN = settings.TEST_TOKEN

# ----- QUIZ STATE ENDPOINT -----
async def quiz_state_endpoint(request):
    return JSONResponse({"active": quiz_state.active})

quizmaster_a2a_app.router.routes.append(
    Route("/quiz_state", endpoint=quiz_state_endpoint, methods=["GET"])
)

# ----- RUN TEST ENDPOINT -----
async def run_test_endpoint(request):
    # Read query parameters
    token = request.query_params.get("token")
    difficulty = request.query_params.get("difficulty")
    num_questions = request.query_params.get("num_questions")
    subject = request.query_params.get("subject")
    topic = request.query_params.get("topic")

    # ---- SECURITY CHECK ----
    if token != TEST_TOKEN:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    # ---- REQUIRED PARAMETERS ----
    if not difficulty:
        return JSONResponse({"error": "Missing required parameter: difficulty"}, status_code=400)

    if not num_questions:
        return JSONResponse({"error": "Missing required parameter: num_questions"}, status_code=400)

    try:
        num_questions = int(num_questions)
    except:
        return JSONResponse({"error": "num_questions must be an integer"}, status_code=400)

    # Require subject OR topic
    if not subject and not topic:
        return JSONResponse(
            {"error": "You must provide at least 'subject' or 'topic'."},
            status_code=400,
        )

    chosen_topic = topic if topic else subject

    # Question count
    question_count = len(ALL_STATIC_QUESTIONS)

    # Try generating quiz
    try:
        quiz_output = start_quiz(chosen_topic, difficulty, num_questions)
        quiz_ok = True
    except Exception as e:
        quiz_output = f"Error generating quiz: {e}"
        quiz_ok = False

    return JSONResponse({
        "status": "ok" if quiz_ok else "error",
        "questions_loaded": question_count,
        "subject_used": subject,
        "topic_used": topic,
        "difficulty_used": difficulty,
        "num_questions_used": num_questions,
        "quiz_generation_success": quiz_ok,
        "sample_quiz_output": quiz_output,
    })

# Register /run_test GET route
quizmaster_a2a_app.router.routes.append(
    Route("/run_test", endpoint=run_test_endpoint, methods=["GET"])
)

# -----------------------------------------------------------
# LOAD QUESTIONS BEFORE STARTUP
# -----------------------------------------------------------
ALL_STATIC_QUESTIONS = _load_static_questions()
logger.info(f"✅ Loaded {len(ALL_STATIC_QUESTIONS)} static questions on startup")

# REQUIRED for Uvicorn
app = quizmaster_a2a_app