"""
F.R.I.D.A.Y. Notes Access — Local JSON storage (cross-platform / Windows).
"""

import os
import json
import logging
from datetime import datetime

log = logging.getLogger("friday.notes")

NOTES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "notes.json")

def _load_notes() -> list[dict]:
    try:
        os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
        if not os.path.exists(NOTES_FILE):
            return []
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"Failed to load notes: {e}")
        return []

def _save_notes(notes: list[dict]):
    try:
        os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log.error(f"Failed to save notes: {e}")

async def get_recent_notes(count: int = 10) -> list[dict]:
    """Get most recent notes (title + creation date)."""
    notes = _load_notes()
    # Sort notes by created_at descending
    notes_sorted = sorted(notes, key=lambda x: x.get("created_at", ""), reverse=True)
    return [
        {
            "title": n.get("title", "Untitled"),
            "date": n.get("created_at", ""),
            "folder": n.get("folder", "Notes")
        }
        for n in notes_sorted[:count]
    ]

async def read_note(title_match: str) -> dict | None:
    """Read a note by title (partial match). Returns title + body."""
    notes = _load_notes()
    title_match_lower = title_match.lower()
    for n in notes:
        if title_match_lower in n.get("title", "").lower():
            return {
                "title": n.get("title", ""),
                "body": n.get("body", "")
            }
    return None

async def search_notes_apple(query: str, count: int = 5) -> list[dict]:
    """Search notes by title keyword."""
    notes = _load_notes()
    query_lower = query.lower()
    results = []
    for n in notes:
        if query_lower in n.get("title", "").lower() or query_lower in n.get("body", "").lower():
            results.append({
                "title": n.get("title", ""),
                "date": n.get("created_at", "")
            })
            if len(results) >= count:
                break
    return results

async def create_apple_note(title: str, body: str, folder: str = "Notes") -> bool:
    """Create a new note."""
    notes = _load_notes()
    new_note = {
        "title": title,
        "body": body,
        "folder": folder,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    notes.append(new_note)
    _save_notes(notes)
    log.info(f"Created Local Note: {title}")
    return True

async def get_note_folders() -> list[str]:
    """Get list of note folder names."""
    notes = _load_notes()
    folders = set(n.get("folder", "Notes") for n in notes)
    if not folders:
        folders.add("Notes")
    return sorted(list(folders))
