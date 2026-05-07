"""Map (app, window title) -> high-level category.

Rules are loaded from ~/.activity_tracker/rules.json if present, otherwise
the built-in defaults below are used. The first matching rule wins, so
order from most specific to least specific.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Built-in defaults. Each rule: substring (case-insensitive) anywhere in
# "{app} | {title}" -> category. Add your own in rules.json to override.
DEFAULT_RULES: list[tuple[str, str]] = [
    # Email / comms
    ("gmail",          "Email"),
    ("outlook",        "Email"),
    ("mail.app",       "Email"),
    ("slack",          "Comms"),
    ("discord",        "Comms"),
    ("zoom",           "Meetings"),
    ("google meet",    "Meetings"),
    ("microsoft teams", "Meetings"),

    # Coding
    ("github",         "Coding"),
    ("gitlab",         "Coding"),
    ("vscode",         "Coding"),
    ("code - ",        "Coding"),     # VS Code window title
    ("intellij",       "Coding"),
    ("pycharm",        "Coding"),
    ("webstorm",       "Coding"),
    ("nvim",           "Coding"),
    ("vim",            "Coding"),
    ("terminal",       "Coding"),
    ("iterm",          "Coding"),
    ("alacritty",      "Coding"),
    ("kitty",          "Coding"),
    ("xterm",          "Coding"),
    ("gnome-terminal", "Coding"),

    # Networking / job hunt
    ("linkedin",       "Networking"),
    ("calendly",       "Networking"),
    ("indeed",         "Job search"),
    ("hired",          "Job search"),
    ("lever.co",       "Job search"),
    ("greenhouse",     "Job search"),

    # Learning / docs
    ("stackoverflow",  "Learning"),
    ("stack overflow", "Learning"),
    ("docs.",          "Learning"),
    ("notion",         "Notes"),
    ("obsidian",       "Notes"),

    # Distractions
    ("youtube",        "Media"),
    ("netflix",        "Media"),
    ("twitch",         "Media"),
    ("spotify",        "Media"),
    ("twitter",        "Social"),
    (" x.com",         "Social"),
    ("reddit",         "Social"),
    ("instagram",      "Social"),

    # AI tools
    ("claude",         "AI tools"),
    ("chatgpt",        "AI tools"),
    ("openai",         "AI tools"),
    ("perplexity",     "AI tools"),

    # Browsers (fallback if URL didn't match anything specific)
    ("chrome",         "Browsing"),
    ("firefox",        "Browsing"),
    ("safari",         "Browsing"),
    ("edge",           "Browsing"),
    ("brave",          "Browsing"),
]


@dataclass
class Categorizer:
    rules: list[tuple[str, str]]

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Categorizer":
        if path is None:
            base = os.environ.get("ACTIVITY_TRACKER_HOME")
            home = Path(base).expanduser() if base else Path.home() / ".activity_tracker"
            path = home / "rules.json"
        if path.exists():
            try:
                data = json.loads(path.read_text())
                rules = [(str(p).lower(), str(c)) for p, c in data]
                return cls(rules=rules)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        return cls(rules=[(p.lower(), c) for p, c in DEFAULT_RULES])

    def classify(self, app: str, title: str, url: Optional[str] = None) -> str:
        haystack = f"{app} | {title} | {url or ''}".lower()
        for pattern, category in self.rules:
            if pattern in haystack:
                return category
        return "Other"


_URL_RE = re.compile(r"https?://[^\s)]+")


def extract_url(title: str) -> Optional[str]:
    """Some browsers put the URL in the title bar; pull it out if present."""
    m = _URL_RE.search(title or "")
    return m.group(0) if m else None
