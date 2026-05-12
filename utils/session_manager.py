import json
import uuid
import os
from datetime import datetime

SESSIONS_DIR = "sessions"


def _ensure_dir():
    os.makedirs(SESSIONS_DIR, exist_ok=True)


def _empty_sop():
    return {
        "chat_history": [],
        "sop_draft": "",
        "sop_title": "",
        "process_diagram": "",
        "automation_suggestions": "",
    }


def migrate_session(session):
    """Migrate flat-key sessions to sops-list structure."""
    if "sops" not in session:
        entry = _empty_sop()
        entry["chat_history"] = session.pop("chat_history", [])
        entry["sop_draft"] = session.pop("sop_draft", "")
        entry["sop_title"] = session.pop("sop_title", "")
        entry["process_diagram"] = session.pop("process_diagram", "")
        entry["automation_suggestions"] = session.pop("automation_suggestions", "")
        session["sops"] = [entry]
        session["active_sop_idx"] = 0
    if "process_plan" not in session:
        session["process_plan"] = []
    return session


def create_session():
    _ensure_dir()
    session_id = str(uuid.uuid4())
    session = {
        "id": session_id,
        "created_at": datetime.now().isoformat(),
        "company": {},
        "sops": [_empty_sop()],
        "active_sop_idx": 0,
        "process_plan": [],
    }
    save_session(session_id, session)
    return session_id, session


def load_session(session_id):
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_session(session_id, data):
    _ensure_dir()
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_sessions():
    _ensure_dir()
    sessions = []
    for fname in os.listdir(SESSIONS_DIR):
        if fname.endswith(".json"):
            data = load_session(fname[:-5])
            if data:
                sessions.append(data)
    return sorted(sessions, key=lambda x: x.get("created_at", ""), reverse=True)
