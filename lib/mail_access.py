"""
F.R.I.D.A.Y. Mail Access — Windows compatible.

Reads Gmail via the Google Gmail API (see email_helper.py for OAuth setup).
The Apple Mail / osascript implementation has been removed.
"""

import logging

log = logging.getLogger("friday.mail")


async def get_unread_count() -> dict:
    """Get unread message count from Gmail."""
    try:
        from email_helper import get_gmail_unread_count
        return await get_gmail_unread_count()
    except Exception as e:
        log.warning(f"get_unread_count failed: {e}")
        return {"total": 0, "accounts": {}}


async def get_recent_messages(count: int = 10) -> list[dict]:
    """Get most recent messages from Gmail inbox."""
    try:
        from email_helper import get_recent_emails
        return await get_recent_emails(count=count)
    except Exception as e:
        log.warning(f"get_recent_messages failed: {e}")
        return []


async def get_unread_messages(count: int = 10) -> list[dict]:
    """Get unread messages from Gmail."""
    try:
        from email_helper import get_recent_emails
        msgs = await get_recent_emails(count=count)
        return [m for m in msgs if not m.get("read", True)]
    except Exception as e:
        log.warning(f"get_unread_messages failed: {e}")
        return []


async def get_messages_from_account(account_name: str, count: int = 10) -> list[dict]:
    """Not applicable for Gmail API — returns recent messages instead."""
    return await get_recent_messages(count=count)


async def search_mail(query: str, count: int = 10) -> list[dict]:
    """Search Gmail by query string."""
    try:
        from email_helper import search_gmail
        return await search_gmail(query=query, count=count)
    except Exception as e:
        log.warning(f"search_mail failed: {e}")
        return []


async def read_message(subject_match: str) -> dict | None:
    """Read a message by subject match."""
    msgs = await search_mail(subject_match, count=1)
    return msgs[0] if msgs else None


async def get_accounts() -> list[str]:
    """Return connected Gmail accounts."""
    return ["Gmail"]


# ---------------------------------------------------------------------------
# Formatters — used by server.py (platform-independent)
# ---------------------------------------------------------------------------

def format_unread_summary(unread: dict) -> str:
    """Format unread counts for voice."""
    total = unread.get("total", 0)
    if total == 0:
        return "Inbox is clear, sir. No unread messages."
    accounts = unread.get("accounts", {})
    parts = [f"{count} in {acct}" for acct, count in accounts.items() if count > 0]
    if len(parts) == 1:
        return f"You have {total} unread {'message' if total == 1 else 'messages'} — {parts[0]}."
    elif parts:
        return f"You have {total} unread messages: {', '.join(parts)}."
    return f"You have {total} unread {'message' if total == 1 else 'messages'}."


def format_messages_for_context(messages: list[dict], label: str = "Recent emails") -> str:
    """Format messages as context for the LLM."""
    if not messages:
        return f"{label}: None."
    lines = [f"{label}:"]
    for m in messages[:10]:
        read_marker = "" if m.get("read") else " [UNREAD]"
        line = f"  - {m.get('sender', '')}: {m.get('subject', '')}{read_marker}"
        if m.get("date"):
            date_str = m["date"]
            if " at " in date_str:
                date_str = date_str.split(" at ")[0].split(", ", 1)[-1] if ", " in date_str else date_str
            line += f" ({date_str})"
        lines.append(line)
    return "\n".join(lines)


def format_messages_for_voice(messages: list[dict]) -> str:
    """Format messages for voice response."""
    if not messages:
        return "No messages to report, sir."
    count = len(messages)
    if count == 1:
        m = messages[0]
        sender = _short_sender(m.get("sender", ""))
        return f"One message from {sender}: {m.get('subject', '')}."
    summaries = []
    for m in messages[:5]:
        sender = _short_sender(m.get("sender", ""))
        summaries.append(f"{sender} regarding {m.get('subject', '')}")
    result = f"You have {count} messages. "
    result += ". ".join(summaries[:3])
    if count > 3:
        result += f". And {count - 3} more."
    return result


def _short_sender(sender: str) -> str:
    """Extract just the name from an email sender string."""
    if "<" in sender:
        return sender.split("<")[0].strip().strip('"')
    if "@" in sender:
        return sender.split("@")[0]
    return sender
