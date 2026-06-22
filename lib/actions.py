"""
F.R.I.D.A.Y. Action Executor — System actions.

Execute actions IMMEDIATELY, before generating any LLM response.
Each function returns {"success": bool, "confirmation": str}.
"""

import asyncio
import logging
import os
import re
import time
from pathlib import Path
from urllib.parse import quote

log = logging.getLogger("friday.actions")

DESKTOP_PATH = Path.home() / "Desktop"

_SKIP_PERMISSIONS = os.getenv("FRIDAY_SKIP_PERMISSIONS", "true").lower() not in ("0", "false", "no")


async def open_terminal(command: str = "") -> dict:
    """Open terminal console window and optionally run a command."""
    import sys
    if sys.platform == "win32":
        import subprocess
        success = False
        try:
            if command:
                subprocess.Popen(["cmd.exe", "/k", command], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(["cmd.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            success = True
        except Exception as e:
            log.error(f"Failed to open terminal on Windows: {e}")
        return {
            "success": success,
            "confirmation": "Terminal is open." if success else "I had trouble opening Terminal.",
        }
    return {"success": False, "confirmation": "Terminal action is not supported on this platform."}


async def open_browser(url: str, browser: str = "chrome") -> dict:
    """Open URL in user's browser."""
    import webbrowser
    success = False
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: webbrowser.open(url))
        success = True
    except Exception as e:
        log.error(f"Failed to open browser: {e}")
    return {
        "success": success,
        "confirmation": "Pulled that up in browser." if success else "I had trouble opening the browser.",
    }


# Keep backward compat
async def open_chrome(url: str) -> dict:
    return await open_browser(url, "chrome")


async def open_claude_in_project(project_dir: str, prompt: str) -> dict:
    """Open Terminal, cd to project dir, run Claude Code interactively."""
    claude_md = Path(project_dir) / "CLAUDE.md"
    claude_md.write_text(f"# Task\n\n{prompt}\n\nBuild this completely. If web app, make index.html work standalone.\n")

    import sys
    if sys.platform == "win32":
        import subprocess
        success = False
        try:
            skip_flag = " --dangerously-skip-permissions" if _SKIP_PERMISSIONS else ""
            cmd = f'cd /d "{project_dir}" && claude{skip_flag}'
            subprocess.Popen(["cmd.exe", "/k", cmd], creationflags=subprocess.CREATE_NEW_CONSOLE)
            success = True
        except Exception as e:
            log.error(f"Failed to open Claude on Windows: {e}")
        return {
            "success": success,
            "confirmation": "Claude Code is running in a new Command Prompt window."
            if success
            else "Had trouble spawning Claude Code.",
        }
    return {"success": False, "confirmation": "Spawning Claude Code in project is not supported on this platform."}


async def monitor_build(project_dir: str, ws=None, synthesize_fn=None) -> None:
    """Monitor a Claude Code build for completion. Notify via WebSocket when done."""
    import base64

    output_file = Path(project_dir) / ".friday_output.txt"
    start = time.time()
    timeout = 600  # 10 minutes

    while time.time() - start < timeout:
        await asyncio.sleep(5)
        if output_file.exists():
            content = output_file.read_text()
            if "--- F.R.I.D.A.Y. TASK COMPLETE ---" in content:
                log.info(f"Build complete in {project_dir}")
                if ws and synthesize_fn:
                    try:
                        msg = "The build is complete."
                        audio_bytes = await synthesize_fn(msg)
                        if audio_bytes:
                            encoded = base64.b64encode(audio_bytes).decode()
                            await ws.send_json({"type": "status", "state": "speaking"})
                            await ws.send_json({"type": "audio", "data": encoded, "text": msg})
                            await ws.send_json({"type": "status", "state": "idle"})
                    except Exception as e:
                        log.warning(f"Build notification failed: {e}")
                return

    log.warning(f"Build timed out in {project_dir}")


# ---------------------------------------------------------------------------
# System Controls — WiFi, Bluetooth, Dark/Light Mode (Windows)
# ---------------------------------------------------------------------------

async def wifi_control(state: str) -> dict:
    """Enable or disable WiFi on Windows using netsh.

    state: 'on' | 'off'
    """
    import sys
    import subprocess

    if sys.platform != "win32":
        return {"success": False, "confirmation": "WiFi control is only supported on Windows."}

    action = "enable" if state == "on" else "disable"
    label  = "enabled" if state == "on" else "disabled"
    try:
        # Find the wireless interface name first
        result = subprocess.run(
            ["netsh", "interface", "show", "interface"],
            capture_output=True, text=True, timeout=5
        )
        # Look for lines mentioning 'Wi-Fi' or 'Wireless'
        iface = None
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                name_parts = parts[3:]
                candidate = " ".join(name_parts)
                if any(k in candidate.lower() for k in ["wi-fi", "wifi", "wireless", "wlan"]):
                    iface = candidate
                    break
        if not iface:
            iface = "Wi-Fi"  # Windows default

        proc = subprocess.run(
            ["netsh", "interface", "set", "interface", iface, action],
            capture_output=True, text=True, timeout=8
        )
        if proc.returncode == 0:
            return {"success": True, "confirmation": f"WiFi {label}."}
        else:
            # Try with admin via PowerShell if plain netsh fails
            ps = f'netsh interface set interface "{iface}" {action}'
            subprocess.Popen(
                ["powershell", "-Command", f'Start-Process cmd -Verb RunAs -ArgumentList "/c {ps}"'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return {"success": True, "confirmation": f"Requesting WiFi {label} — you may need to approve a permission prompt."}
    except Exception as e:
        log.error(f"WiFi control failed: {e}")
        return {"success": False, "confirmation": f"I had trouble toggling WiFi."}


async def bluetooth_control(state: str) -> dict:
    """Enable or disable Bluetooth on Windows via PowerShell device manager.

    state: 'on' | 'off'
    """
    import sys
    import subprocess

    if sys.platform != "win32":
        return {"success": False, "confirmation": "Bluetooth control is only supported on Windows."}

    label = "enabled" if state == "on" else "disabled"
    action_verb = "Enable" if state == "on" else "Disable"
    try:
        ps_script = (
            f'$bt = Get-PnpDevice | Where-Object {{$_.Class -eq "Bluetooth" -and '
            f'$_.FriendlyName -notlike "*Microsoft Bluetooth*"}} | Select-Object -First 1;'
            f'if ($bt) {{ {action_verb}-PnpDevice -InstanceId $bt.InstanceId -Confirm:$false; '
            f'Write-Output "OK" }} else {{ Write-Output "NOT_FOUND" }}'
        )
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=15
        )
        out = result.stdout.strip()
        if "OK" in out or result.returncode == 0:
            return {"success": True, "confirmation": f"Bluetooth {label}."}
        elif "NOT_FOUND" in out:
            # Fallback: toggle via registry + radio manager
            reg_val = 2 if state == "off" else 1  # 2=disabled, 1=enabled
            ps2 = (
                f'$regPath = "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\bthserv";'
                f'Set-ItemProperty -Path $regPath -Name Start -Value {reg_val};'
                f'Write-Output "OK"'
            )
            subprocess.run(
                ["powershell", "-Command",
                 f'Start-Process powershell -Verb RunAs -ArgumentList "-Command {ps2}" -WindowStyle Hidden'],
                capture_output=True, timeout=5
            )
            return {"success": True, "confirmation": f"Requesting Bluetooth {label} — you may need to approve a prompt."}
        else:
            return {"success": False, "confirmation": f"I had trouble toggling Bluetooth."}
    except Exception as e:
        log.error(f"Bluetooth control failed: {e}")
        return {"success": False, "confirmation": f"I had trouble toggling Bluetooth."}


async def dark_mode_toggle(mode: str) -> dict:
    """Switch Windows between dark and light theme.

    mode: 'dark' | 'light'
    """
    import sys
    import subprocess

    if sys.platform != "win32":
        return {"success": False, "confirmation": "Theme control is only supported on Windows."}

    # Registry value: 0=dark, 1=light
    val = 1 if mode == "light" else 0
    label = "light" if mode == "light" else "dark"

    try:
        reg_path = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        # Set both Apps theme and System (taskbar/Start) theme
        for key in ["AppsUseLightTheme", "SystemUsesLightTheme"]:
            subprocess.run(
                ["reg", "add", reg_path, "/v", key, "/t", "REG_DWORD", "/d", str(val), "/f"],
                capture_output=True, timeout=5
            )
        return {"success": True, "confirmation": f"Switched to {label} mode."}
    except Exception as e:
        log.error(f"Dark mode toggle failed: {e}")
        return {"success": False, "confirmation": "I had trouble changing the theme."}


async def execute_action(intent: dict, projects: list = None) -> dict:
    """Route a classified intent to the right action function.

    Args:
        intent: {"action": str, "target": str} from classify_intent()
        projects: list of known project dicts for resolving working dirs

    Returns: {"success": bool, "confirmation": str, "project_dir": str | None}
    """
    action = intent.get("action", "chat")
    target = intent.get("target", "")

    if action == "open_terminal":
        claude_cmd = "claude --dangerously-skip-permissions" if _SKIP_PERMISSIONS else "claude"
        result = await open_terminal(claude_cmd)
        result["project_dir"] = None
        return result

    elif action == "browse":
        if target.startswith("http://") or target.startswith("https://"):
            url = target
        else:
            url = f"https://www.google.com/search?q={quote(target)}"

        result = await open_browser(url)
        result["project_dir"] = None
        return result

    elif action == "build":
        # Create project folder on Desktop, spawn Claude Code
        project_name = _generate_project_name(target)
        project_dir = str(DESKTOP_PATH / project_name)
        os.makedirs(project_dir, exist_ok=True)
        result = await open_claude_in_project(project_dir, target)
        result["project_dir"] = project_dir
        return result

    elif action == "open_app":
        result = await open_app(target)
        result["project_dir"] = None
        return result

    elif action == "write_notepad":
        result = await write_notepad(target)
        result["project_dir"] = None
        return result

    elif action == "media":
        result = await media_control(target)
        result["project_dir"] = None
        return result

    else:
        return {"success": False, "confirmation": "", "project_dir": None}


def _generate_project_name(prompt: str) -> str:
    """Generate a kebab-case project folder name from the prompt."""
    # First: check for a quoted name like "tiktok-analytics-dashboard"
    quoted = re.search(r'"([^"]+)"', prompt)
    if quoted:
        name = quoted.group(1).strip()
        # Already kebab-case or close to it
        name = re.sub(r"[^a-zA-Z0-9\s-]", "", name).strip()
        if name:
            return re.sub(r"[\s]+", "-", name.lower())

    # Second: check for "called X" or "named X" pattern
    called = re.search(r'(?:called|named)\s+(\S+(?:[-_]\S+)*)', prompt, re.IGNORECASE)
    if called:
        name = re.sub(r"[^a-zA-Z0-9-]", "", called.group(1))
        if len(name) > 3:
            return name.lower()

    # Fallback: extract meaningful words
    words = re.sub(r"[^a-zA-Z0-9\s]", "", prompt.lower()).split()
    skip = {"a", "the", "an", "me", "build", "create", "make", "for", "with", "and",
            "to", "of", "i", "want", "need", "new", "project", "directory", "called",
            "on", "desktop", "that", "application", "app", "full", "stack", "simple",
            "web", "page", "site", "named"}
    meaningful = [w for w in words if w not in skip and len(w) > 2][:4]
    return "-".join(meaningful) if meaningful else "friday-project"


async def open_app(app_name: str) -> dict:
    """Open an installed application on the user's computer."""
    import sys
    import subprocess
    success = False
    
    app_clean = app_name.strip().lower()
    
    # Common Windows executable mappings
    windows_mappings = {
        "vs code": "code",
        "vscode": "code",
        "visual studio code": "code",
        "notepad": "notepad",
        "calculator": "calc",
        "paint": "mspaint",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "browser": "chrome",
        "google chrome": "chrome",
        "firefox": "firefox",
        "edge": "msedge",
        "spotify": "spotify",
        "slack": "slack",
        "discord": "discord",
        "zoom": "zoom",
    }
    
    if sys.platform == "win32":
        cmd_target = windows_mappings.get(app_clean, app_clean)
        try:
            subprocess.Popen(f'start "" "{cmd_target}"', shell=True)
            success = True
        except Exception as e:
            log.error(f"Failed to open app {app_clean} (mapped: {cmd_target}) on Windows: {e}")
    else:
        try:
            subprocess.Popen([app_clean])
            success = True
        except Exception as e:
            log.error(f"Failed to open app {app_clean} on non-Windows: {e}")

    return {
        "success": success,
        "confirmation": f"Opening {app_name}." if success else f"I had trouble opening {app_name}."
    }


async def write_notepad(text: str) -> dict:
    """Write text to a temporary text file and open it in Notepad on Windows."""
    import sys
    import tempfile
    import subprocess
    from pathlib import Path
    
    success = False
    if sys.platform == "win32":
        try:
            desktop = Path.home() / "Desktop"
            if desktop.exists():
                file_path = desktop / "F.R.I.D.A.Y._Note.txt"
            else:
                file_path = Path(tempfile.gettempdir()) / "F.R.I.D.A.Y._Note.txt"
                
            file_path.write_text(text, encoding="utf-8")
            subprocess.Popen(f'start notepad.exe "{file_path}"', shell=True)
            success = True
            confirmation = f"I've written that in Notepad. It is saved as F.R.I.D.A.Y._Note.txt on your Desktop."
        except Exception as e:
            log.error(f"Failed to write in Notepad: {e}")
            confirmation = "I ran into an issue writing to Notepad."
    else:
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
                f.write(text.encode("utf-8"))
                tmp_path = f.name
            subprocess.Popen(["xdg-open", tmp_path])
            success = True
            confirmation = "I've opened the text in your editor."
        except Exception:
            confirmation = "Action not supported on this platform."
            
    return {"success": success, "confirmation": confirmation}


async def media_control(action: str) -> dict:
    """Control system media playback (play/pause, next, previous, stop)."""
    import pyautogui
    success = False
    action_clean = action.strip().lower()
    
    # Map friendly action names to PyAutoGUI key names
    key_map = {
        "playpause": "playpause",
        "play_pause": "playpause",
        "next": "nexttrack",
        "next_track": "nexttrack",
        "previous": "prevtrack",
        "prev_track": "prevtrack",
        "stop": "stop",
    }
    
    key_target = key_map.get(action_clean)
    if not key_target:
        return {
            "success": False,
            "confirmation": f"Unknown media action: {action}."
        }
        
    try:
        pyautogui.press(key_target)
        success = True
        confirmations = {
            "playpause": "Toggled playback.",
            "nexttrack": "Skipping to the next track.",
            "prevtrack": "Going back to the previous track.",
            "stop": "Stopped playback.",
        }
        confirmation = confirmations.get(key_target, "Media adjusted.")
    except Exception as e:
        log.error(f"Failed to execute media control action {action} ({key_target}): {e}")
        confirmation = f"I had trouble controlling the media."
        
    return {"success": success, "confirmation": confirmation}
