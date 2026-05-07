# activity_tracker

Local-first, free desktop activity tracker. It samples the foreground
window every few seconds, categorizes it (Coding / Email / Meetings /
Networking / etc.), and turns the day into a Markdown snippet you can
paste into a GitHub profile, dev journal, or demo description.

Everything stays on your machine. SQLite + Python stdlib only — no
`pip install` required, no network calls, no account.

## Quick start

```bash
# one-shot: track in background + dashboard at http://127.0.0.1:8765
python -m activity_tracker run -v
```

Or run them separately:

```bash
python -m activity_tracker track    # start in the morning, leave running
python -m activity_tracker serve    # opens dashboard
python -m activity_tracker summary  # text summary in terminal
python -m activity_tracker snippet  # Markdown snippet to stdout
python -m activity_tracker note "Shipped activity tracker MVP"
```

Add `--day 2026-05-06` to any read command to look at a past day.

## Platform notes

- **Linux (X11):** install `xdotool` (active-window probe) and
  `xprintidle` (idle detection). Both are in every major distro's
  package manager.
- **macOS:** uses `osascript` and `ioreg`, both built in. The first run
  will prompt for "System Events" automation permission.
- **Windows:** uses `user32`/`psapi` via `ctypes`, no install needed.

If a probe is unavailable, the tracker logs a skip and keeps running.

## Customizing categories

Drop a `rules.json` next to the database (default
`~/.activity_tracker/rules.json`). Format: a list of
`[substring, category]` pairs, first match wins.

```json
[
  ["github.com/your-org", "Work"],
  ["leetcode", "Interview prep"],
  ["calendly", "Networking"]
]
```

## Files

| File | What it does |
| ---- | ------------ |
| `window.py` | OS-specific active-window + idle probes |
| `storage.py` | SQLite store; merges adjacent same-context samples |
| `categorize.py` | Rule-based (app, title, url) → category |
| `tracker.py` | Polling loop |
| `summary.py` | Day aggregation + Markdown snippet renderer |
| `server.py` | 127.0.0.1 dashboard (HTML + JSON API) |
| `__main__.py` | `python -m activity_tracker <cmd>` CLI |

## Why this is enough

You asked for the same thing Velo does: record what you do, show where
the time went, and produce shareable end-of-day output. This delivers
that without a subscription, account, or anything leaving your laptop.
