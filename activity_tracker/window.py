"""Cross-platform active window + idle-time probes.

Each probe returns ``None`` if it can't determine a value (missing tool,
locked screen, headless session, etc.) so the tracker can degrade gracefully
instead of crashing. We deliberately shell out to OS utilities rather than
pulling in heavy GUI bindings -- this keeps the app pip-install-free.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class WindowInfo:
    app: str           # process / bundle name, e.g. "firefox"
    title: str         # window title, e.g. "Inbox (32) - Gmail"
    url: Optional[str] = None  # browser URL when extractable from title


def _run(cmd: list[str], timeout: float = 1.5) -> Optional[str]:
    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


# ---------------------------------------------------------------------------
# Linux (X11)

def _linux_window() -> Optional[WindowInfo]:
    if not shutil.which("xdotool"):
        return None
    wid = _run(["xdotool", "getactivewindow"])
    if not wid:
        return None
    title = _run(["xdotool", "getwindowname", wid]) or ""
    pid = _run(["xdotool", "getwindowpid", wid])
    app = ""
    if pid:
        try:
            with open(f"/proc/{pid}/comm") as f:
                app = f.read().strip()
        except OSError:
            pass
    return WindowInfo(app=app or "unknown", title=title)


def _linux_idle_seconds() -> Optional[float]:
    out = _run(["xprintidle"])
    if out is None:
        return None
    try:
        return int(out) / 1000.0
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# macOS

_MAC_SCRIPT = '''
tell application "System Events"
  set frontApp to first application process whose frontmost is true
  set appName to name of frontApp
  try
    set winName to name of first window of frontApp
  on error
    set winName to ""
  end try
end tell
return appName & "\\n" & winName
'''


def _mac_window() -> Optional[WindowInfo]:
    if not shutil.which("osascript"):
        return None
    out = _run(["osascript", "-e", _MAC_SCRIPT])
    if not out:
        return None
    parts = out.split("\n", 1)
    app = parts[0].strip()
    title = parts[1].strip() if len(parts) > 1 else ""
    return WindowInfo(app=app, title=title)


def _mac_idle_seconds() -> Optional[float]:
    out = _run(["sh", "-c", "ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print $NF/1000000000; exit}'"])
    try:
        return float(out) if out else None
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Windows

def _win_window() -> Optional[WindowInfo]:
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return None
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return None
    length = user32.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    title = buf.value
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    app = "unknown"
    try:
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        kernel32 = ctypes.windll.kernel32
        psapi = ctypes.windll.psapi
        h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if h:
            try:
                exe_buf = ctypes.create_unicode_buffer(512)
                psapi.GetModuleFileNameExW(h, 0, exe_buf, 512)
                app = os.path.basename(exe_buf.value) or "unknown"
            finally:
                kernel32.CloseHandle(h)
    except OSError:
        pass
    return WindowInfo(app=app, title=title)


def _win_idle_seconds() -> Optional[float]:
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return None

    class LASTINPUTINFO(ctypes.Structure):
        _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

    info = LASTINPUTINFO()
    info.cbSize = ctypes.sizeof(info)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
        return None
    millis = ctypes.windll.kernel32.GetTickCount() - info.dwTime
    return millis / 1000.0


# ---------------------------------------------------------------------------
# Public API

def active_window() -> Optional[WindowInfo]:
    if sys.platform.startswith("linux"):
        return _linux_window()
    if sys.platform == "darwin":
        return _mac_window()
    if sys.platform == "win32":
        return _win_window()
    return None


def idle_seconds() -> Optional[float]:
    if sys.platform.startswith("linux"):
        return _linux_idle_seconds()
    if sys.platform == "darwin":
        return _mac_idle_seconds()
    if sys.platform == "win32":
        return _win_idle_seconds()
    return None
