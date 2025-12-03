from tutor.config import settings
import json
import os
import time
from google.oauth2 import service_account
from google.cloud import firestore
from typing import Dict, Any, Optional

def init_firestore_client():
    """
    Initialize Firestore in two modes:

    (1) Local development:
        Load service account JSON from FIRESTORE_CREDENTIALS_JSON_PATH.

    (2) Cloud Run:
        Automatically load from Secret Manager mount or ADC.

    Returns: firestore.Client() or None if unavailable.
    """

    path = settings.FIRESTORE_CREDENTIALS_JSON_PATH

    # ---------- CASE 1: Load credentials from JSON file ----------
    if path:
        try:
            if os.path.exists(path):
                print(f"🔥 Loading Firestore credentials from file: {path}")
                with open(path, "r") as f:
                    creds_dict = json.load(f)

                creds = service_account.Credentials.from_service_account_info(creds_dict)
                return firestore.Client(credentials=creds, project=creds_dict["project_id"])
            else:
                print(f"⚠️ FIRESTORE_CREDENTIALS_JSON_PATH file not found: {path}")
        except Exception as e:
            print("❌ Failed to load Firestore credentials from file:", e)
            print("👉 Falling back to ADC...")

    # ---------- CASE 2: Cloud Run ADC ----------
    try:
        print("🔥 Using Application Default Credentials (Cloud Run mode)")
        return firestore.Client()
    except Exception as e:
        print("❌ Firestore ADC failed:", e)
        print("👉 Using IN-MEMORY fallback mode.")
        return None


db = init_firestore_client()

# ============================================================
# Memory Manager
# ============================================================

class PersistentMemory:
    """
    Firestore-backed OR in-memory fallback persistent memory manager.
    """

    # ---------------------------------------------------------
    # FS PATH HELPERS
    # ---------------------------------------------------------

    def _user_ref(self, uid: str):
        if not db:
            return None
        return db.collection("users").document(uid)

    def _session_ref(self, uid: str):
        if not db:
            return None
        return self._user_ref(uid).collection("session")

    def _state_ref(self, uid: str):
        if not db:
            return None
        return self._session_ref(uid).document("state")

    def _messages_ref(self, uid: str):
        if not db:
            return None
        return self._state_ref(uid).collection("messages")

    # ============================================================
    # IN-MEMORY FALLBACK STORAGE (only used if Firestore offline)
    # ============================================================
    _local_store = {}

    def _ensure_local_user(self, uid):
        if uid not in self._local_store:
            self._local_store[uid] = {
                "state": {
                    "current_subject": None,
                    "current_topic": None,
                    "long_term_summary": None,
                },
                "messages": []
            }

    # ============================================================
    # PUBLIC API — SAME AS BEFORE
    # ============================================================

    def load_user_state(self, uid: str) -> dict:
        print("MEMORY ----> Entered load_user_state")

        if not db:
            # In-memory mode
            self._ensure_local_user(uid)
            loc = self._local_store[uid]
            return {
                "current_subject": loc["state"]["current_subject"],
                "current_topic": loc["state"]["current_topic"],
                "long_term_summary": loc["state"]["long_term_summary"],
                "short_term_messages": loc["messages"][-20:],  # last 20
            }

        # --- Firestore mode ---
        mem = {
            "current_subject": None,
            "current_topic": None,
            "long_term_summary": None,
            "short_term_messages": [],
        }

        state_doc = self._state_ref(uid).get()
        if state_doc.exists:
            data = state_doc.to_dict()
            mem["current_subject"] = data.get("current_subject")
            mem["current_topic"] = data.get("current_topic")
            mem["long_term_summary"] = data.get("long_term_summary")

        # Load messages
        msg_docs = (
            self._messages_ref(uid)
            .order_by("ts", direction=firestore.Query.DESCENDING)
            .limit(20)
            .stream()
        )

        msgs = [d.to_dict() for d in msg_docs]
        mem["short_term_messages"] = list(reversed(msgs))
        return mem

    def save_state(self, uid: str, subject: str, topic: str, long_summary: Optional[str] = None):
        print("MEMORY ----> Entered save_state")

        if not db:
            self._ensure_local_user(uid)
            self._local_store[uid]["state"].update(
                {
                    "current_subject": subject,
                    "current_topic": topic,
                    "long_term_summary": long_summary,
                }
            )
            return

        self._state_ref(uid).set(
            {
                "current_subject": subject,
                "current_topic": topic,
                "long_term_summary": long_summary,
                "last_updated": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

    def append_message(self, uid: str, role: str, text: str):
        print("MEMORY ----> Entered append_message")
        ts = time.time()

        if not db:
            self._ensure_local_user(uid)
            self._local_store[uid]["messages"].append(
                {"role": role, "text": text, "ts": ts}
            )
            return

        doc_id = f"msg_{int(ts * 1000)}"
        self._messages_ref(uid).document(doc_id).set(
            {"role": role, "text": text, "ts": ts}
        )

    def summarize_short_term(self, uid: str, limit: int = 10) -> str:
        print("MEMORY ----> summarise last messages")

        if not db:
            self._ensure_local_user(uid)
            msgs = self._local_store[uid]["messages"][-limit:]
            if not msgs:
                return "No previous conversation found."
            rows = [f"{m['role']}: {m['text']}" for m in msgs]
            return "Summary of recent interactions:\n" + "\n".join(rows)

        # Firestore mode
        msg_docs = (
            self._messages_ref(uid)
            .order_by("ts", direction=firestore.Query.DESCENDING)
            .limit(limit)
            .stream()
        )
        msgs = [d.to_dict() for d in msg_docs]
        if not msgs:
            return "No previous conversation found."

        msgs = list(reversed(msgs))
        rows = [f"{m['role']}: {m['text']}" for m in msgs]
        return "Summary of recent interactions:\n" + "\n".join(rows)

    def update_long_term_summary(self, uid: str, summary: str):
        print("MEMORY ----> write long term memory")

        if not db:
            self._ensure_local_user(uid)
            self._local_store[uid]["state"]["long_term_summary"] = summary
            return

        self._state_ref(uid).set(
            {"long_term_summary": summary, "last_updated": firestore.SERVER_TIMESTAMP},
            merge=True,
        )

    # Debug
    def dump_user_state(self, uid: str):
        return self.load_user_state(uid)