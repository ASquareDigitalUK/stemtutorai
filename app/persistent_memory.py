"""
Firestore-backed persistent memory manager.
Phase-1: Stores/loads user session state + short-term messages.
Phase-2 ready: Includes structure/hooks for mastery, progress, quiz logging.
"""
import time
from typing import Dict, Any, List, Optional
from google.cloud import firestore

# -------------------------------------------------
# Initialize Firestore Client
# -------------------------------------------------
# Assumes: GOOGLE_APPLICATION_CREDENTIALS is set
db = firestore.Client()


# =================================================
# FIRESTORE DOCUMENT STRUCTURE
# =================================================
# /users/{uid}/memory/state
# /users/{uid}/memory/messages/msg_001
#
# Future (Phase-2):
# /users/{uid}/progress/subjects/{subject}/...
# /users/{uid}/quiz_history/{quiz_id}/...
# =================================================


class PersistentMemory:
    """A Firestore-backed persistent memory manager."""

    # ----------------------------
    # FIRESTORE PATH HELPERS
    # ----------------------------

    def _user_ref(self, uid: str):
        return db.collection("users").document(uid)

    def _session_ref(self, uid: str):
        # /users/{uid}/session/
        return self._user_ref(uid).collection("session")

    def _state_ref(self, uid: str):
        # /users/{uid}/session/state
        return self._session_ref(uid).document("state")

    def _messages_ref(self, uid: str):
        # /users/{uid}/session/state/messages/
        return self._state_ref(uid).collection("messages")

    # =================================================
    # PHASE-1 METHODS
    # =================================================

    # ----------------------------
    # 1. LOAD FULL MEMORY STATE
    # ----------------------------
    def load_user_state(self, uid: str) -> Dict[str, Any]:
        """Load memory/state + up to last 20 messages."""
        print("MEMORY ----> Entered load_user_state")
        mem = {
            "current_subject": None,
            "current_topic": None,
            "long_term_summary": None,
            "short_term_messages": [],
        }

        # Load state
        state_doc = self._state_ref(uid).get()
        if state_doc.exists:
            data = state_doc.to_dict()
            mem["current_subject"] = data.get("current_subject")
            mem["current_topic"] = data.get("current_topic")
            mem["long_term_summary"] = data.get("long_term_summary")

        # Load last 20 messages sorted by timestamp
        msg_docs = (
            self._messages_ref(uid)
            .order_by("ts", direction=firestore.Query.DESCENDING)
            .limit(20)
            .stream()
        )

        messages = []
        for d in msg_docs:
            messages.append(d.to_dict())

        # Reverse so oldest → newest
        mem["short_term_messages"] = list(reversed(messages))
        return mem

    # ----------------------------
    # 2. SAVE STATE
    # ----------------------------
    def save_state(self, uid: str, subject: str, topic: str, long_summary: Optional[str] = None):
        """Save user topic/subject context."""
        print("MEMORY ----> Entered save_state")
        self._state_ref(uid).set(
            {
                "current_subject": subject,
                "current_topic": topic,
                "long_term_summary": long_summary,
                "last_updated": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

    # ----------------------------
    # 3. APPEND A MESSAGE
    # ----------------------------
    def append_message(self, uid: str, role: str, text: str):
        """Stores a short-term message into Firestore."""
        print("MEMORY ----> Entered append_message")
        ts = time.time()
        doc_id = f"msg_{int(ts * 1000)}"
        self._messages_ref(uid).document(doc_id).set(
            {
                "role": role,
                "text": text,
                "ts": ts,
            }
        )

    # ----------------------------
    # 4. SUMMARIZE LAST N MESSAGES
    # ----------------------------
    def summarize_short_term(self, uid: str, limit: int = 10) -> str:
        print("MEMORY ----> Entered summarise last 10 messages")
        msg_docs = (
            self._messages_ref(uid)
            .order_by("ts", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )

        messages = []
        for d in msg_docs:
            messages.append(d.to_dict())

        if not messages:
            return "No previous conversation found."

        # Reverse chronological order
        messages = list(reversed(messages))

        lines = [f"{m['role']}: {m['text']}" for m in messages]
        return "Summary of recent interactions:\n" + "\n".join(lines)

    # ----------------------------
    # 5. WRITE LONG-TERM SUMMARY
    # ----------------------------
    def update_long_term_summary(self, uid: str, summary: str):
        print("MEMORY ----> write long term memory")
        self._state_ref(uid).set(
            {
                "long_term_summary": summary,
                "last_updated": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

    # =================================================
    # PHASE-2 PLACEHOLDERS (Not implemented yet)
    # =================================================

    def record_quiz_attempt(self, uid: str, quiz_data: Dict[str, Any]):
        """
        Placeholder for Phase-2.
        Store quiz score/results under: /users/{uid}/quiz_history/
        """
        quiz_id = f"quiz_{int(time.time() * 1000)}"
        self._user_ref(uid).collection("quiz_history").document(quiz_id).set(quiz_data)

    def update_mastery(self, uid: str, subject: str, topic: str, delta: float):
        """
        Placeholder for Phase-2 mastery model.
        Adjust mastery_score & compute new level.
        """
        subj_ref = (
            self._user_ref(uid)
            .collection("progress")
            .document("subjects")
            .collection(subject)
            .document(topic)
        )
        # Future: read, update mastery, save back.

    # =================================================
    # DEBUG ACCESS
    # =================================================

    def dump_user_state(self, uid: str):
        """Return the full Firestore snapshot for debugging."""
        return self.load_user_state(uid)