import os
import json

from fastapi import FastAPI
from pydantic import BaseModel

from app.agent_runtime import runner, memory
from app.classifier_agent_runtime import classifier_runner
from app.intent_classifier_agent import intent_classifier_runner
from app.quizmaster_server import quizmaster_a2a_app
from app.logging_plugin import logging_plugin
from app.quizmaster_tool import (
    is_quiz_active,
    get_supported_subjects,
    get_topic_examples,
)

# ----------------------------------------------------
# Global config
# ----------------------------------------------------
DEBUG_ENABLED = os.getenv("ADK_DEBUG", "1") == "1"

app = FastAPI()

# Mount the Quizmaster A2A app under /quizmaster
app.mount("/quizmaster", quizmaster_a2a_app)

if DEBUG_ENABLED:
    print("✅ Quizmaster A2A mounted at /quizmaster")


# ----------------------------------------------------
# Request model
# ----------------------------------------------------
class Query(BaseModel):
    user_id: str
    message: str


# ----------------------------------------------------
# Utility: Extract reply text from ADK events
# ----------------------------------------------------
def extract_final_reply(events):
    """
    Walk over ADK events and pull out the final text reply.

    Priority:
    1) stateDelta.reply (ADK canonical place)
    2) content.parts[*].text (fallback)

    Always returns a string (possibly ""), never None.
    """
    events = list(events)

    # 1) ADK-style reply: actions.stateDelta["reply"]
    for e in events:
        actions = getattr(e, "actions", None)
        if not actions:
            continue

        state_delta = getattr(actions, "stateDelta", None)
        if isinstance(state_delta, dict):
            reply = state_delta.get("reply")
            if reply:
                return reply

    # 2) Fallback: content.parts[*].text
    for e in events:
        content = getattr(e, "content", None)
        if not content:
            continue

        parts = getattr(content, "parts", None)
        if not parts or not isinstance(parts, list):
            continue

        for p in parts:
            if not p:
                continue
            text = getattr(p, "text", None)
            if text:
                return text

    # Critical: never return None (prevents downstream Pydantic issues)
    return ""


# ----------------------------------------------------
# QUIZ STATE CHECK (local helper)
# ----------------------------------------------------
def is_quiz_active_local() -> bool:
    """
    Safe wrapper around is_quiz_active(), never throws.
    """
    try:
        return bool(is_quiz_active())
    except Exception:
        return False


# ----------------------------------------------------
# Helper: Subject/topic classification for quiz flow
# ----------------------------------------------------
def classify_subject_and_topic(msg: str):
    """
    Calls the SubjectClassifier and returns (subject, topic, confidence).
    subject/topic are normalised to simple strings or None.

    Currently used as a helper; kept as-is for future routing logic.
    """
    subject = None
    topic = None
    conf = 0.0

    try:
        # Local sync runner variant (used where async isn't convenient)
        cls_events = classifier_runner.run_debug_sync(msg)
    except AttributeError:
        # If run_debug_sync isn't available, fail gracefully
        return subject, topic, conf

    raw_reply = extract_final_reply(cls_events)
    if not raw_reply:
        return subject, topic, conf

    raw = raw_reply.strip().replace("```json", "").replace("```", "").strip()
    try:
        parsed = json.loads(raw)
        subject = parsed.get("subject")
        topic = parsed.get("topic")
        conf = float(parsed.get("confidence", 0.0))
    except Exception:
        pass

    if isinstance(subject, str):
        subject = subject.strip() or None
    else:
        subject = None

    if isinstance(topic, str):
        topic = topic.strip() or None
    else:
        topic = None

    return subject, topic, conf


# ----------------------------------------------------
# /welcome endpoint
# ----------------------------------------------------
@app.post("/welcome")
async def welcome_endpoint(query: Query):
    uid = (query.user_id or "").strip() or "anonymous"

    state = memory.dump_user_state(uid)
    short_msgs = state.get("short_term_messages", [])
    is_new = len(short_msgs) == 0

    if is_new:
        stitched = f"""
You are an AI Tutor greeting a NEW student named {uid}.
Generate a warm, encouraging welcome message (1–2 sentences).
"""
    else:
        summary = memory.summarize_short_term(uid)
        stitched = f"""
You are an AI Tutor greeting a RETURNING student named {uid}.
Here is a summary of your recent interactions with them:\n{summary}
Generate a short, friendly WELCOME BACK message (1–2 sentences).
"""

    events = await runner.run_debug(stitched, session_id=uid)
    reply = extract_final_reply(events) or "Hello! 👋"

    memory.append_message(uid, "assistant", reply)
    return {"welcome": reply}


# ----------------------------------------------------
# /tutor endpoint
# ----------------------------------------------------
@app.post("/tutor")
async def tutor_endpoint(query: Query):
    uid = (query.user_id or "").strip() or "anonymous"
    msg = (query.message or "").strip()

    if not msg:
        return {"response": "Say something to begin!", "memory_debug": {}}

    # ------------------------------------------------
    # QUIZ-MODE SAFETY OVERRIDE
    # ------------------------------------------------
    quiz_active = is_quiz_active_local()
    short_msg = msg.lower().strip()
    forced_intent = None

    # Very short messages during an active quiz are treated as answers
    if quiz_active and (short_msg in ["a", "b", "c", "d"] or len(short_msg) <= 3):
        forced_intent = "quiz_answer_forced"

    # ------------------------------------------------
    # INTENT CLASSIFICATION
    # ------------------------------------------------
    intent = "off_topic"
    intent_conf = 0.0

    if forced_intent is None:
        intent_events = await intent_classifier_runner.run_debug(msg)
        intent_raw = extract_final_reply(intent_events)
        if intent_raw:
            parsed_text = (
                intent_raw.strip()
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )
            try:
                parsed = json.loads(parsed_text)
                intent = parsed.get("intent", "off_topic")
                intent_conf = parsed.get("confidence", 0.0)
            except Exception:
                pass
    else:
        intent = forced_intent

    if DEBUG_ENABLED:
        print(f"[ORCH] uid={uid}, intent={intent}, quiz_active={quiz_active}, msg={msg}")

    # ------------------------------------------------
    # A) Forced quiz answer (short message while quiz active)
    # ------------------------------------------------
    if intent == "quiz_answer_forced":
        memory.append_message(uid, "user", msg)

        stitched_prompt = f"""
The user answered the quiz question with: "{msg}"

You MUST call the answer_question tool with exactly this string:
    "{msg}"

Do not reinterpret or modify the student's answer.
"""
        events = await runner.run_debug(stitched_prompt, session_id=uid)
        reply = (
            extract_final_reply(events)
            or "I tried to check your answer, but something went wrong. Please try again."
        )
        memory.append_message(uid, "assistant", reply)
        return {
            "response": reply,
            "memory_debug": memory.dump_user_state(uid),
        }

    # ------------------------------------------------
    # B) Greeting  (NO MEMORY SUMMARY)
    # ------------------------------------------------
    if intent == "greeting":
        memory.append_message(uid, "user", msg)
        stitched_prompt = f"""
The user greeted you: "{msg}"
Respond with a short, warm reply and keep it friendly.
"""
        events = await runner.run_debug(stitched_prompt, session_id=uid)
        reply = extract_final_reply(events) or "Hi there! 👋"
        memory.append_message(uid, "assistant", reply)
        return {
            "response": reply,
            "memory_debug": memory.dump_user_state(uid),
        }

    # ------------------------------------------------
    # C) Small talk (NO MEMORY SUMMARY)
    # ------------------------------------------------
    if intent == "small_talk":
        memory.append_message(uid, "user", msg)
        stitched_prompt = f"""
The user is making small talk: "{msg}"
Respond politely and briefly, keeping the tone warm.
"""
        events = await runner.run_debug(stitched_prompt, session_id=uid)
        reply = (
            extract_final_reply(events)
            or "That's nice! Now, what would you like to learn today?"
        )
        memory.append_message(uid, "assistant", reply)
        return {
            "response": reply,
            "memory_debug": memory.dump_user_state(uid),
        }

    # ------------------------------------------------
    # D) Quiz answer (classifier says so)  (NO SUMMARY)
    # ------------------------------------------------
    if intent == "quiz_answer":
        memory.append_message(uid, "user", msg)

        stitched_prompt = f"""
The user answered the quiz question with: "{msg}"

You MUST call the answer_question tool with exactly this input:
    "{msg}"

Do not generate questions or score yourself.
Only the quiz tools handle quiz state.
"""
        events = await runner.run_debug(stitched_prompt, session_id=uid)
        reply = (
            extract_final_reply(events)
            or "I tried to check your answer, but something went wrong. Please try again."
        )
        memory.append_message(uid, "assistant", reply)
        return {
            "response": reply,
            "memory_debug": memory.dump_user_state(uid),
        }

    # ------------------------------------------------
    # E) User requests a quiz  (NO SUMMARY)
    # ------------------------------------------------
    if intent == "request_quiz":
        memory.append_message(uid, "user", msg)

        # Use SubjectClassifier to see if they gave a subject, a topic, or both.
        cls_events = await classifier_runner.run_debug(msg)
        cls_raw = extract_final_reply(cls_events)

        subject = None
        topic = None
        conf = 0.0

        if cls_raw:
            raw = cls_raw.strip().replace("```json", "").replace("```", "").strip()
            try:
                parsed = json.loads(raw)
                subject = parsed.get("subject")
                topic = parsed.get("topic")
                conf = float(parsed.get("confidence", 0.0))
            except Exception:
                pass

        if isinstance(subject, str):
            subject = subject.strip() or None
        else:
            subject = None

        if isinstance(topic, str):
            topic = topic.strip() or None
        else:
            topic = None

        # Normalise subject to lower for hint lookup
        subject_lower = subject.lower() if subject else None

        # Case 1: user only gave a broad subject (e.g. "maths", "science")
        generic_subject_words = {"math", "maths", "mathematics", "science"}
        if (
            (topic is None or topic.lower() in generic_subject_words)
            and subject_lower in generic_subject_words
        ):
            examples = get_topic_examples(
                "math" if "math" in subject_lower else "science"
            )
            examples_text = ""
            if examples:
                examples_text = (
                    "\nHere are some example topics you can choose from:\n- "
                    + "\n- ".join(examples[:7])
                )
            reply = (
                f"{subject} covers a lot of ground! 📚\n\n"
                "Could you tell me a more specific topic for your quiz?\n"
                "For example, you might say something like:\n"
                '"linear equations", "fractions", "probability", or "geometry".'
                f"{examples_text}"
            )
            memory.append_message(uid, "assistant", reply)
            return {
                "response": reply,
                "memory_debug": memory.dump_user_state(uid),
            }

        # Case 2: user gave a topic (with or without subject) → start quiz on TOPIC
        if topic:
            stitched_prompt = f"""
The user asked to start a quiz. Original message: "{msg}"

You MUST call the start_quiz tool with these parameters:
- topic: "{topic}"
- difficulty: "easy"
- num_questions: 5

Do NOT generate your own questions.
Let the quiz engine handle question selection and scoring.
"""
        else:
            # No reliable topic from classifier → fall back to using full message as topic
            stitched_prompt = f"""
The user asked to start a quiz: "{msg}"

You MUST call the start_quiz tool, providing:
- topic: a short phrase describing the quiz topic based on the user's request
- difficulty: "easy" by default
- num_questions: 5 by default

Do NOT generate your own questions.
Let the quiz engine handle question selection.
"""

        events = await runner.run_debug(stitched_prompt, session_id=uid)
        reply = (
            extract_final_reply(events)
            or "I tried to start a quiz, but something went wrong. Please try rephrasing your request."
        )
        memory.append_message(uid, "assistant", reply)
        return {
            "response": reply,
            "memory_debug": memory.dump_user_state(uid),
        }

    # ------------------------------------------------
    # F) Academic question (ONLY PATH THAT USES MEMORY SUMMARY)
    # ------------------------------------------------
    if intent == "academic_question":
        # Run subject classifier
        cls_events = await classifier_runner.run_debug(msg)
        cls_raw = extract_final_reply(cls_events)

        subject = None
        topic = None
        if cls_raw:
            raw = cls_raw.strip().replace("```json", "").replace("```", "").strip()
            try:
                parsed = json.loads(raw)
                subject = parsed.get("subject")
                topic = parsed.get("topic")
            except Exception:
                pass

        # Save state + user message
        memory.save_state(uid, subject, topic)
        memory.append_message(uid, "user", msg)

        summary = memory.summarize_short_term(uid)

        topic_info = ""
        if subject or topic:
            topic_info = (
                f"\nStudent is currently learning: subject={subject}, topic={topic}.\n"
            )

        stitched_prompt = f"""
{summary}
{topic_info}
User says: "{msg}"

Respond as the tutor using ONLY this memory context.
Explain clearly, step-by-step, and be encouraging.
"""

        events = await runner.run_debug(stitched_prompt, session_id=uid)
        reply = extract_final_reply(events) or "I'm not sure how to respond."
        memory.append_message(uid, "assistant", reply)

        return {
            "response": reply,
            "memory_debug": memory.dump_user_state(uid),
        }

    # ------------------------------------------------
    # G) Off-topic fallback (NO SUMMARY)
    # ------------------------------------------------
    memory.append_message(uid, "user", msg)
    stitched_prompt = f"""
The user said something off-topic: "{msg}"
Please reply kindly and guide them back to learning-related topics or quizzes.
"""
    events = await runner.run_debug(stitched_prompt, session_id=uid)
    reply = (
        extract_final_reply(events)
        or "Let's get back to learning! What subject or topic would you like help with?"
    )
    memory.append_message(uid, "assistant", reply)

    return {
        "response": reply,
        "memory_debug": memory.dump_user_state(uid),
    }


print(
    "🚀 fastapi_server.py READY — Orchestrator with Firestore + quiz tools + smarter quiz routing loaded."
)