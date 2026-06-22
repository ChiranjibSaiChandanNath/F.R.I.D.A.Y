"""
F.R.I.D.A.Y. Browser Control — voice-driven browser tab management.

Uses pyautogui (keyboard shortcuts) + pygetwindow (window focus).
Works with any browser: Chrome, Firefox, Edge.

Supported commands:
  scroll up / scroll down
  next tab / previous tab
  new tab / close tab
  go back / go forward
  refresh / reload
  zoom in / zoom out
  open incognito
  click <text>             — click element whose visible text matches
  click first/second/...   — click the Nth search result / video / song
  open first result        — same as click first
  play first song          — same as click first
  type <text>              — type text into the currently focused field
  press enter / escape     — keyboard key presses
"""

import asyncio
import logging
import sys
import time

log = logging.getLogger("friday.browser_control")

# Browser window title keywords to search for (in priority order)
_BROWSER_TITLES = ["Google Chrome", "Chrome", "Mozilla Firefox", "Firefox",
                   "Microsoft Edge", "Edge", "Brave", "Opera"]


def _focus_browser() -> bool:
    """Find an open browser window and bring it to focus.

    Returns True if a browser window was found and focused, False otherwise.
    Only works on Windows (pygetwindow is Windows-only).
    """
    if sys.platform != "win32":
        return False

    try:
        import pygetwindow as gw
        for title_keyword in _BROWSER_TITLES:
            windows = gw.getWindowsWithTitle(title_keyword)
            if windows:
                win = windows[0]
                try:
                    if win.isMinimized:
                        win.restore()
                    win.activate()
                    time.sleep(0.3)  # wait for window to come to front
                    return True
                except Exception:
                    continue
        return False
    except ImportError:
        log.warning("pygetwindow not installed. Run: pip install pygetwindow")
        return False
    except Exception as e:
        log.error(f"Window focus failed: {e}")
        return False


async def _send_shortcut(focus_first: bool = True, *keys) -> dict:
    """Focus browser then fire a keyboard shortcut."""
    if sys.platform != "win32":
        return {"success": False, "confirmation": "Browser control is only supported on Windows."}

    try:
        import pyautogui
        pyautogui.FAILSAFE = False

        loop = asyncio.get_running_loop()

        def _do():
            if focus_first:
                found = _focus_browser()
                if not found:
                    return False
                time.sleep(0.15)
            if len(keys) == 1:
                pyautogui.press(keys[0])
            else:
                pyautogui.hotkey(*keys)
            return True

        result = await loop.run_in_executor(None, _do)
        return {"success": result, "confirmation": None}

    except ImportError:
        log.warning("pyautogui not installed. Run: pip install pyautogui")
        return {"success": False, "confirmation": "pyautogui is not installed. Run: pip install pyautogui"}
    except Exception as e:
        log.error(f"Shortcut failed: {e}")
        return {"success": False, "confirmation": "Something went wrong with browser control."}


# ---------------------------------------------------------------------------
# Public API — one function per action
# ---------------------------------------------------------------------------

async def scroll_down(amount: int = 3) -> str:
    for _ in range(amount):
        r = await _send_shortcut(True, "pagedown")
        if not r["success"]:
            return r["confirmation"] or "Browser not found."
    return "Scrolling down."


async def scroll_up(amount: int = 3) -> str:
    for _ in range(amount):
        r = await _send_shortcut(True, "pageup")
        if not r["success"]:
            return r["confirmation"] or "Browser not found."
    return "Scrolling up."


async def next_tab() -> str:
    r = await _send_shortcut(True, "ctrl", "tab")
    if not r["success"]:
        return r["confirmation"] or "Couldn't switch tab, sir."
    return "Next tab."


async def prev_tab() -> str:
    r = await _send_shortcut(True, "ctrl", "shift", "tab")
    if not r["success"]:
        return r["confirmation"] or "Couldn't switch tab, sir."
    return "Previous tab."


async def new_tab() -> str:
    r = await _send_shortcut(True, "ctrl", "t")
    if not r["success"]:
        return r["confirmation"] or "Couldn't open a new tab, sir."
    return "New tab opened."


async def close_tab() -> str:
    r = await _send_shortcut(True, "ctrl", "w")
    if not r["success"]:
        return r["confirmation"] or "Couldn't close the tab, sir."
    return "Tab closed."


async def go_back() -> str:
    r = await _send_shortcut(True, "alt", "left")
    if not r["success"]:
        return r["confirmation"] or "Couldn't go back, sir."
    return "Going back."


async def go_forward() -> str:
    r = await _send_shortcut(True, "alt", "right")
    if not r["success"]:
        return r["confirmation"] or "Couldn't go forward, sir."
    return "Going forward."


async def refresh_page() -> str:
    r = await _send_shortcut(True, "f5")
    if not r["success"]:
        return r["confirmation"] or "Couldn't refresh, sir."
    return "Page refreshed."


async def zoom_in() -> str:
    r = await _send_shortcut(True, "ctrl", "+")
    if not r["success"]:
        return r["confirmation"] or "Couldn't zoom in, sir."
    return "Zoomed in."


async def zoom_out() -> str:
    r = await _send_shortcut(True, "ctrl", "-")
    if not r["success"]:
        return r["confirmation"] or "Couldn't zoom out, sir."
    return "Zoomed out."


async def zoom_reset() -> str:
    r = await _send_shortcut(True, "ctrl", "0")
    if not r["success"]:
        return r["confirmation"] or "Couldn't reset zoom, sir."
    return "Zoom reset."


async def open_incognito() -> str:
    r = await _send_shortcut(True, "ctrl", "shift", "n")
    if not r["success"]:
        return r["confirmation"] or "Couldn't open incognito, sir."
    return "Incognito window opened."


async def focus_address_bar() -> str:
    r = await _send_shortcut(True, "ctrl", "l")
    if not r["success"]:
        return r["confirmation"] or "Couldn't focus the address bar, sir."
    return "Address bar focused."


# ---------------------------------------------------------------------------
# Click-by-text — finds and clicks a browser element whose label matches text
# ---------------------------------------------------------------------------

def _find_element_by_text_uia(search_text: str):
    """Use Windows UI Automation via ctypes (no comtypes needed) to find an element.

    Uses the raw IUIAutomation COM interface through ctypes.
    Returns (x, y) center coordinates or None.
    """
    try:
        import ctypes
        import ctypes.wintypes as wt

        # ── IUIAutomation via raw COM ──────────────────────────────────────
        # We instantiate via CoCreateInstance with the known CLSIDs/IIDs.
        # This works on any Windows 7+ machine with UIAutomation installed.
        CLSID_CUIAutomation = "{ff48dba4-60ef-4201-aa87-54103eef594e}"
        IID_IUIAutomation   = "{30cbe57d-d9d0-452a-ab13-7ac5ac4825ee}"

        ole32 = ctypes.windll.ole32
        ole32.CoInitializeEx(None, 0)  # COINIT_APARTMENTTHREADED

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", ctypes.c_ulong),
                ("Data2", ctypes.c_ushort),
                ("Data3", ctypes.c_ushort),
                ("Data4", ctypes.c_ubyte * 8),
            ]

        def _guid(s):
            import uuid
            u = uuid.UUID(s)
            b = u.bytes_le
            g = GUID()
            g.Data1 = int.from_bytes(b[0:4], "little")
            g.Data2 = int.from_bytes(b[4:6], "little")
            g.Data3 = int.from_bytes(b[6:8], "little")
            for i in range(8):
                g.Data4[i] = b[8 + i]
            return g

        clsid = _guid(CLSID_CUIAutomation)
        iid   = _guid(IID_IUIAutomation)

        # Try CoCreateInstance
        p = ctypes.c_void_p()
        hr = ole32.CoCreateInstance(
            ctypes.byref(clsid),
            None,
            1,  # CLSCTX_INPROC_SERVER
            ctypes.byref(iid),
            ctypes.byref(p),
        )
        if hr != 0 or not p:
            return None

        # ── Use PowerShell UIA wrapper (simpler & more reliable) ────────────
        # Rather than hand-rolling vtable calls, delegate to a PS1-liner
        # that uses the .NET UIA assembly (always available on Windows).
        return _find_element_powershell(search_text)

    except Exception as exc:
        log.debug(f"UIA ctypes init failed: {exc}")
        return _find_element_powershell(search_text)


def _find_element_powershell(search_text: str):
    """Use PowerShell + .NET UIAutomation to find element by name.

    Returns (x, y) center or None.
    .NET System.Windows.Automation is available on all modern Windows.
    """
    try:
        import subprocess, json

        # PowerShell script: walk the UI tree of the foreground window,
        # find the first element whose Name contains our search text,
        # and output its center X,Y coordinates as JSON.
        ps_script = r"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$needle = '{needle}'
$ae = [System.Windows.Automation.AutomationElement]
$root = $ae::RootElement
$hw = [System.IntPtr][System.Runtime.InteropServices.Marshal]::GetActiveObject -ErrorAction SilentlyContinue
# Use GetForegroundWindow
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {{
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}}
"@
$hwnd = [Win32]::GetForegroundWindow()
$elem = $ae::FromHandle($hwnd)
$cond = [System.Windows.Automation.Condition]::TrueCondition
$scope = [System.Windows.Automation.TreeScope]::Descendants
$all = $elem.FindAll($scope, $cond)
foreach ($e in $all) {{
    $name = $e.Current.Name
    if ($name -and $name.ToLower().Contains($needle.ToLower())) {{
        $rect = $e.Current.BoundingRectangle
        if ($rect.Width -gt 0 -and $rect.Height -gt 0) {{
            $cx = [int]($rect.Left + $rect.Width / 2)
            $cy = [int]($rect.Top + $rect.Height / 2)
            Write-Output "$cx,$cy"
            exit
        }}
    }}
}}
""".replace("{needle}", search_text.replace("'", "''"))

        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, text=True, timeout=8
        )
        out = result.stdout.strip()
        if out and "," in out:
            parts = out.split(",")
            return (int(parts[0]), int(parts[1]))
        return None
    except Exception as exc:
        log.debug(f"PowerShell UIA search failed: {exc}")
        return None


def _find_element_by_ocr(search_text: str):
    """Screenshot the screen and use OpenCV + PIL to find text by template.

    Since pytesseract may not be installed, we try two approaches:
    1. pytesseract (if available)
    2. easyocr (if available)
    Returns (x, y) or None.
    """
    # Try pytesseract first
    try:
        import pyautogui
        import pytesseract

        screenshot = pyautogui.screenshot()
        data = pytesseract.image_to_data(
            screenshot, output_type=pytesseract.Output.DICT, config="--psm 11"
        )
        needle = search_text.lower()
        for i, word in enumerate(data["text"]):
            if word and needle in word.lower() and int(data["conf"][i]) > 30:
                x = data["left"][i] + data["width"][i] // 2
                y = data["top"][i] + data["height"][i] // 2
                return (x, y)
        return None
    except Exception:
        pass

    # Try easyocr as fallback
    try:
        import pyautogui
        import numpy as np
        import easyocr

        screenshot = pyautogui.screenshot()
        img_np = np.array(screenshot)
        reader = easyocr.Reader(["en"], gpu=False)
        results = reader.readtext(img_np)
        needle = search_text.lower()
        for (bbox, text, conf) in results:
            if needle in text.lower() and conf > 0.3:
                # bbox is [[tl_x, tl_y], [tr_x, tr_y], [br_x, br_y], [bl_x, bl_y]]
                xs = [p[0] for p in bbox]
                ys = [p[1] for p in bbox]
                cx = int(sum(xs) / len(xs))
                cy = int(sum(ys) / len(ys))
                return (cx, cy)
        return None
    except Exception as exc:
        log.debug(f"OCR click search failed: {exc}")
        return None


async def click_text(text: str) -> str:
    """Click a browser element whose visible text matches the given string.

    Strategy (in order):
    1. Windows UI Automation via PowerShell — most reliable.
    2. pytesseract / easyocr OCR screenshot scan — fallback.
    """
    if sys.platform != "win32":
        return "Clicking is only supported on Windows."

    try:
        import pyautogui
        pyautogui.FAILSAFE = False

        loop = asyncio.get_running_loop()

        def _do():
            # Focus the browser first
            if not _focus_browser():
                return None
            time.sleep(0.2)

            # Try UI Automation first (fastest, most accurate)
            coords = _find_element_by_text_uia(text)

            # Fallback to OCR if UIA failed
            if coords is None:
                coords = _find_element_by_ocr(text)

            return coords

        coords = await loop.run_in_executor(None, _do)

        if coords is None:
            return "Nothing found on the page."

        def _click():
            pyautogui.click(coords[0], coords[1])

        await loop.run_in_executor(None, _click)
        return "Clicked."

    except ImportError:
        return "pyautogui is not installed. Run: pip install pyautogui"
    except Exception as e:
        log.error(f"click_text failed: {e}")
        return "Something went wrong while trying to click."


# Ordinal word → index (1-based)
_ORDINALS = {
    "first": 1, "1st": 1, "one": 1, "1": 1,
    "second": 2, "2nd": 2, "two": 2, "2": 2,
    "third": 3, "3rd": 3, "three": 3, "3": 3,
    "fourth": 4, "4th": 4, "four": 4, "4": 4,
    "fifth": 5, "5th": 5, "five": 5, "5": 5,
    "sixth": 6, "6th": 6, "six": 6, "6": 6,
    "seventh": 7, "7th": 7, "seven": 7, "7": 7,
    "eighth": 8, "8th": 8, "eight": 8, "8": 8,
    "ninth": 9, "9th": 9, "nine": 9, "9": 9,
    "tenth": 10, "10th": 10, "ten": 10, "10": 10,
}


def _find_nth_link_powershell(n: int):
    """Use PowerShell + .NET UIAutomation to find the Nth content link.

    Skips navigation/header links (those near the very top of the screen)
    and returns the center (x, y) of the Nth result link.
    Returns (x, y) or None.
    """
    try:
        import subprocess

        # PowerShell: enumerate all Hyperlink control-type elements in the
        # foreground window, filter to those in the content area (y > 150px
        # to skip navigation bars), sort by vertical position, pick the Nth.
        ps_script = f"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32Help {{
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}}
"@
$hwnd = [Win32Help]::GetForegroundWindow()
$ae   = [System.Windows.Automation.AutomationElement]
$elem = $ae::FromHandle($hwnd)
$cond = New-Object System.Windows.Automation.PropertyCondition(
    $ae::ControlTypeProperty,
    [System.Windows.Automation.ControlType]::Hyperlink
)
$scope   = [System.Windows.Automation.TreeScope]::Descendants
$all     = $elem.FindAll($scope, $cond)
$results = @()
foreach ($e in $all) {{
    $rect = $e.Current.BoundingRectangle
    # Skip links in the top navigation bar (y < 150) and invisible links
    if ($rect.Top -gt 150 -and $rect.Width -gt 10 -and $rect.Height -gt 10) {{
        $results += [PSCustomObject]@{{
            Top  = $rect.Top
            CX   = [int]($rect.Left + $rect.Width / 2)
            CY   = [int]($rect.Top + $rect.Height / 2)
            Name = $e.Current.Name
        }}
    }}
}}
$sorted = $results | Sort-Object Top
$idx    = {n} - 1   # convert to 0-based
if ($sorted.Count -gt $idx) {{
    $item = $sorted[$idx]
    Write-Output "$($item.CX),$($item.CY)"
}} else {{
    Write-Output "NOT_FOUND"
}}
"""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True, text=True, timeout=10
        )
        out = result.stdout.strip()
        log.debug(f"nth_link PS output: {out!r}")
        if out and "," in out and "NOT_FOUND" not in out:
            parts = out.split(",")
            return (int(parts[0]), int(parts[1]))
        return None
    except Exception as exc:
        log.debug(f"nth_link powershell failed: {exc}")
        return None


async def click_nth(n: int) -> str:
    """Click the Nth content link/result visible in the browser.

    Works on YouTube search results, Google results, news feeds, etc.
    n is 1-based (1 = first result).
    """
    if sys.platform != "win32":
        return "Clicking is only supported on Windows."

    ordinal_words = {1: "first", 2: "second", 3: "third", 4: "fourth",
                     5: "fifth", 6: "sixth", 7: "seventh", 8: "eighth"}
    label = ordinal_words.get(n, f"#{n}")

    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        loop = asyncio.get_running_loop()

        def _do():
            if not _focus_browser():
                return None
            time.sleep(0.3)
            return _find_nth_link_powershell(n)

        coords = await loop.run_in_executor(None, _do)

        if coords is None:
            # Fallback: use keyboard — Tab enough times then Enter
            # YouTube: pressing Tab from the page skips to first result
            log.info(f"nth link not found via UIA, trying Tab+Enter fallback")
            import pyautogui
            pyautogui.FAILSAFE = False

            def _tab_fallback():
                if not _focus_browser():
                    return False
                time.sleep(0.2)
                # Press Escape first to clear any focused search box
                pyautogui.press("escape")
                time.sleep(0.1)
                # Tab into content area (skip navigation links)
                # YouTube typically needs ~6-8 tabs to reach first result
                for _ in range(max(1, n) * 3 + 5):
                    pyautogui.press("tab")
                    time.sleep(0.05)
                pyautogui.press("enter")
                return True

            await loop.run_in_executor(None, _tab_fallback)
            return f"Opened the {label} result."

        def _click():
            pyautogui.click(coords[0], coords[1])

        await loop.run_in_executor(None, _click)
        return f"Opening the {label} result."

    except Exception as e:
        log.error(f"click_nth failed: {e}")
        return f"Had trouble clicking that result."


async def type_text(text: str) -> str:
    """Type text into the currently focused field in the browser."""
    if sys.platform != "win32":
        return "Typing is only supported on Windows."

    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        loop = asyncio.get_running_loop()

        def _do():
            _focus_browser()
            time.sleep(0.15)
            pyautogui.typewrite(text, interval=0.04)

        await loop.run_in_executor(None, _do)
        return "Typed."
    except ImportError:
        return "pyautogui is not installed."
    except Exception as e:
        log.error(f"type_text failed: {e}")
        return "Couldn't type that."


async def press_enter() -> str:
    """Press the Enter key in the focused browser."""
    r = await _send_shortcut(True, "enter")
    if not r["success"]:
        return r["confirmation"] or "Couldn't press Enter, sir."
    return "Done."


async def press_escape() -> str:
    """Press the Escape key in the focused browser."""
    r = await _send_shortcut(True, "escape")
    if not r["success"]:
        return r["confirmation"] or "Couldn't press Escape, sir."
    return "Done."


async def press_tab() -> str:
    """Press the Tab key in the focused browser."""
    r = await _send_shortcut(True, "tab")
    if not r["success"]:
        return r["confirmation"] or "Couldn't press Tab, sir."
    return "Done."


# ---------------------------------------------------------------------------
# Dispatcher — maps a command string to an action
# ---------------------------------------------------------------------------

_COMMAND_MAP = {
    # scroll
    "scroll down":       scroll_down,
    "scroll up":         scroll_up,
    "page down":         scroll_down,
    "page up":           scroll_up,
    # tabs
    "next tab":          next_tab,
    "previous tab":      prev_tab,
    "prev tab":          prev_tab,
    "new tab":           new_tab,
    "close tab":         close_tab,
    "open new tab":      new_tab,
    # navigation
    "go back":           go_back,
    "go forward":        go_forward,
    "back":              go_back,
    "forward":           go_forward,
    # refresh
    "refresh":           refresh_page,
    "reload":            refresh_page,
    "refresh page":      refresh_page,
    "reload page":       refresh_page,
    # zoom
    "zoom in":           zoom_in,
    "zoom out":          zoom_out,
    "zoom reset":        zoom_reset,
    "reset zoom":        zoom_reset,
    # other
    "incognito":         open_incognito,
    "open incognito":    open_incognito,
    "private window":    open_incognito,
    "address bar":       focus_address_bar,
    "focus address bar": focus_address_bar,
    "search bar":        focus_address_bar,
    # keyboard
    "press enter":       press_enter,
    "hit enter":         press_enter,
    "enter":             press_enter,
    "press escape":      press_escape,
    "escape":            press_escape,
    "press tab":         press_tab,
}

# Prefix patterns that take a text argument (parsed in execute())
_PREFIX_COMMANDS = [
    ("click on ",    click_text),
    ("click ",       click_text),
    ("press ",       click_text),   # "press Login" etc.
    ("tap ",         click_text),
    ("select ",      click_text),
    ("type ",        type_text),
    ("write ",       type_text),
    ("search for ",  type_text),
]


# Ordinal word → index (1-based)
_ORDINALS = {
    "first": 1, "1st": 1, "one": 1, "1": 1,
    "second": 2, "2nd": 2, "two": 2, "2": 2,
    "third": 3, "3rd": 3, "three": 3, "3": 3,
    "fourth": 4, "4th": 4, "four": 4, "4": 4,
    "fifth": 5, "5th": 5, "five": 5, "5": 5,
    "sixth": 6, "6th": 6, "six": 6, "6": 6,
    "seventh": 7, "7th": 7, "seven": 7, "7": 7,
    "eighth": 8, "8th": 8, "eight": 8, "8": 8,
    "ninth": 9, "9th": 9, "nine": 9, "9": 9,
    "tenth": 10, "10th": 10, "ten": 10, "10": 10,
}


async def execute(command: str) -> str:
    """Execute a browser control command by name.

    Handles fixed commands (scroll down, refresh…), parametric text
    commands (click <text>, type <text>), and positional ordinal
    commands (click first, open second result, play third song).
    """
    cmd = command.strip().lower()

    # ── Ordinal / positional click first (before prefix matching) ──────
    # Matches: "click first", "click first song", "open first result",
    #          "play second", "open the third video", "click on 2nd"
    import re as _exec_re
    _ord_m = _exec_re.match(
        r"(?:click\s+(?:on\s+)?(?:the\s+)?|open\s+(?:the\s+)?|play\s+(?:the\s+)?|select\s+(?:the\s+)?)?"
        r"(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
        r"1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|[1-9]|10)"
        r"(?:\s+(?:song|video|result|link|item|one|option|track|entry|thumbnail|card|row))?$",
        cmd,
    )
    if _ord_m:
        ordinal_word = _ord_m.group(1)
        n = _ORDINALS.get(ordinal_word, 1)
        return await click_nth(n)

    # ── Fixed command exact match ──────────────────────────────────────
    fn = _COMMAND_MAP.get(cmd)
    if fn:
        return await fn()

    # ── Parametric prefix commands ─────────────────────────────────────
    for prefix, handler in _PREFIX_COMMANDS:
        if cmd.startswith(prefix):
            arg_raw = command[len(prefix):].strip()  # preserve original case
            if not arg_raw:
                continue
            # Check if the argument is an ordinal phrase — route to click_nth
            _arg_ord = _exec_re.match(
                r"(?:the\s+)?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
                r"1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|[1-9]|10)"
                r"(?:\s+(?:song|video|result|link|item|one|option|track|entry|thumbnail|card))?$",
                arg_raw.lower(),
            )
            if _arg_ord and handler in (click_text,):
                n = _ORDINALS.get(_arg_ord.group(1), 1)
                return await click_nth(n)
            # Normal text-based click/type
            return await handler(arg_raw)

    return f"I don't know the browser command '{command}', sir."
