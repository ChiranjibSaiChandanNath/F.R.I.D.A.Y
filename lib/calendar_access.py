"""
F.R.I.D.A.Y. Calendar Access — Windows compatible.

Reads Google Calendar via the Google API (see email_helper.py for OAuth setup).
Falls back to empty results if no credentials are present.
"""

import logging
from datetime import datetime, timedelta

log = logging.getLogger("friday.calendar")

# In-memory cache populated by the background refresh thread
_event_cache: list[dict] = []
_cache_time: float = 0


async def refresh_cache():
    """Refresh calendar events from Google Calendar API."""
    global _event_cache, _cache_time
    try:
        from email_helper import get_todays_calendar_events
        events = await get_todays_calendar_events()
        if events is not None:
            _event_cache = events
            import time
            _cache_time = time.time()
            log.info(f"Calendar cache refreshed: {len(_event_cache)} events")
    except Exception as e:
        log.warning(f"Calendar refresh failed: {e}")


async def get_todays_events() -> list[dict]:
    """Return today's cached events."""
    if not _event_cache and _cache_time == 0:
        await refresh_cache()
    return _event_cache


async def get_upcoming_events(hours: int = 4) -> list[dict]:
    """Return events in the next N hours."""
    events = await get_todays_events()
    now = datetime.now()
    cutoff = now + timedelta(hours=hours)
    return [
        e for e in events
        if not e.get("all_day") and e.get("start_dt") and now <= e["start_dt"] <= cutoff
    ]


async def get_next_event() -> dict | None:
    """Return the single next upcoming event."""
    events = await get_upcoming_events(hours=24)
    return events[0] if events else None


def format_events_for_context(events: list[dict]) -> str:
    """Format events as context for the LLM."""
    if not events:
        return "No events scheduled today."
    lines = []
    for evt in events:
        if evt.get("all_day"):
            entry = f"  All day — {evt['title']}"
        else:
            entry = f"  {evt.get('start', '')} — {evt['title']}"
        if evt.get("calendar"):
            entry += f" [{evt['calendar']}]"
        lines.append(entry)
    return "\n".join(lines)


def format_schedule_summary(events: list[dict]) -> str:
    """Format a brief voice-friendly summary of the schedule."""
    if not events:
        return "Your schedule is clear today, sir."
    count = len(events)
    if count == 1:
        evt = events[0]
        if evt.get("all_day"):
            return f"You have one all-day event: {evt['title']}."
        return f"You have one event: {evt['title']} at {evt.get('start', '')}."
    summaries = []
    for evt in events[:5]:
        if evt.get("all_day"):
            summaries.append(f"{evt['title']} all day")
        else:
            summaries.append(f"{evt['title']} at {evt.get('start', '')}")
    result = f"You have {count} events today. "
    result += ". ".join(summaries[:3])
    if count > 3:
        result += f". And {count - 3} more."
    return result
