"""
F.R.I.D.A.Y. Screen Awareness — see what's on the user's screen.

Two capabilities:
1. Window/app list via Windows APIs (fast, text-based)
2. Screenshot via Pillow → Claude vision API (sees everything)
"""

import asyncio
import base64
import json
import logging
import tempfile
from pathlib import Path

log = logging.getLogger("friday.screen")


async def get_active_windows() -> list[dict]:
    """Get list of visible windows with app name, window title, and position.

    Uses ctypes on Windows.
    Returns list of {"app": str, "title": str, "frontmost": bool}.
    """
    import sys
    if sys.platform == "win32":
        return await asyncio.to_thread(_get_windows_win32)
    return []


def _get_windows_win32() -> list[dict]:
    import ctypes
    from ctypes import wintypes
    from pathlib import Path
    
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    windows = []
    foreground_hwnd = user32.GetForegroundWindow()
    
    def enum_windows_callback(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                title_buffer = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, title_buffer, length + 1)
                title = title_buffer.value
                
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                
                app_name = "Unknown"
                h_process = kernel32.OpenProcess(0x1000, False, pid.value)  # PROCESS_QUERY_LIMITED_INFORMATION
                if h_process:
                    path_buffer = ctypes.create_unicode_buffer(1024)
                    size = wintypes.DWORD(1024)
                    if kernel32.QueryFullProcessImageNameW(h_process, 0, path_buffer, ctypes.byref(size)):
                        app_name = Path(path_buffer.value).name.replace(".exe", "")
                    kernel32.CloseHandle(h_process)
                
                if title and app_name not in ("ApplicationFrameHost", "SystemSettings"):
                    windows.append({
                        "app": app_name,
                        "title": title,
                        "frontmost": hwnd == foreground_hwnd
                    })
        return True

    user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
    return windows


async def get_running_apps() -> list[str]:
    """Get list of running application names (visible only)."""
    import sys
    if sys.platform == "win32":
        windows = await get_active_windows()
        return sorted(list(set(w["app"] for w in windows if w["app"] != "Unknown")))
    return []


async def take_screenshot(display_only: bool = True) -> str | None:
    """Take a screenshot and return base64-encoded PNG.

    Args:
        display_only: If True, capture main display only. If False, all displays.

    Returns:
        Base64-encoded PNG string, or None on failure.
    """
    import sys
    try:
        from PIL import ImageGrab
    except ImportError:
        log.warning("Pillow is not installed. Run 'pip install pillow' to enable screenshot support.")
        return None

    try:
        loop = asyncio.get_running_loop()
        if sys.platform == "win32":
            grab_fn = lambda: ImageGrab.grab(all_screens=not display_only)
        else:
            grab_fn = ImageGrab.grab
        
        img = await loop.run_in_executor(None, grab_fn)
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_path = f.name

        try:
            await loop.run_in_executor(None, lambda: img.save(tmp_path, format="PNG"))
            data = Path(tmp_path).read_bytes()
            log.info(f"Screenshot captured via Pillow: {len(data)} bytes")
            return base64.b64encode(data).decode()
        except Exception as e:
            log.warning(f"Saving screenshot failed: {e}")
            return None
        finally:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
    except Exception as e:
        log.warning(f"Screenshot error via Pillow: {e}")
        return None


async def describe_screen(anthropic_client) -> str:
    """Describe what's on the user's screen.

    Tries screenshot + vision first. Falls back to window list + LLM summary.
    """
    # Try screenshot + vision
    screenshot_b64 = await take_screenshot()
    if screenshot_b64 and anthropic_client:
        try:
            response = await anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                system=(
                    "You are F.R.I.D.A.Y. analyzing a screenshot of the user's desktop. "
                    "Describe what you see concisely: which apps are open, what the user "
                    "appears to be working on, any notable content visible. "
                    "Be specific about app names, file names, URLs, code, or documents visible. "
                    "2-4 sentences max. No markdown."
                ),
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": "What's on my screen right now?",
                        },
                    ],
                }],
            )
            return response.content[0].text
        except Exception as e:
            log.warning(f"Vision call failed, falling back to window list: {e}")

    # Fallback: get window list and have LLM summarize
    windows = await get_active_windows()
    apps = await get_running_apps()

    if not windows and not apps:
        return "I wasn't able to see your screen, sir. Screen recording permission may be needed."

    # Build a text description for LLM to summarize
    context_parts = []
    if windows:
        for w in windows:
            marker = " (ACTIVE)" if w["frontmost"] else ""
            context_parts.append(f"{w['app']}: {w['title']}{marker}")

    if apps:
        window_apps = set(w["app"] for w in windows) if windows else set()
        bg_apps = [a for a in apps if a not in window_apps]
        if bg_apps:
            context_parts.append(f"Background apps: {', '.join(bg_apps)}")

    if anthropic_client and context_parts:
        try:
            response = await anthropic_client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                system=(
                    "You are F.R.I.D.A.Y.. Given the user's open windows and apps, summarize "
                    "what they appear to be working on in 1-2 sentences. Natural voice, no markdown."
                ),
                messages=[{"role": "user", "content": "Open windows:\n" + "\n".join(context_parts)}],
            )
            return response.content[0].text
        except Exception:
            pass

    # Raw fallback
    if windows:
        active = next((w for w in windows if w["frontmost"]), None)
        result = f"You have {len(windows)} windows open across {len(set(w['app'] for w in windows))} apps."
        if active:
            result += f" Currently focused on {active['app']}: {active['title']}."
        return result

    return f"Running apps: {', '.join(apps)}. Couldn't read window titles, sir."


def format_windows_for_context(windows: list[dict]) -> str:
    """Format window list as context string for the LLM."""
    if not windows:
        return ""
    lines = ["Currently open on your desktop:"]
    for w in windows:
        marker = " (active)" if w["frontmost"] else ""
        lines.append(f"  - {w['app']}: {w['title']}{marker}")
    return "\n".join(lines)
