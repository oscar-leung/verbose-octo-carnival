import json
import os

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)
client = anthropic.Anthropic()

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """You write cold emails that get replies. You have sent tens of thousands of them through GMass and Apollo and seen what works: specific, short, one clear ask, and a personalization hook that proves the sender actually looked at the recipient before hitting send.

Your job: given a recipient profile and the sender's pitch, write ONE personalized cold email plus three subject lines.

Rules:
1. Subject lines: under 50 characters, lowercase-friendly, no clickbait, no emojis. At least one should reference something specific about the recipient (their company, role, or something in their profile).
2. Email body: 75-140 words. Hard limit 150.
3. Opening line must reference a specific detail from the recipient's profile — not "I saw your company is doing great work" but something concrete (a shipped feature, a recent post, a specific project, their tenure, a detail from their bio). If the profile is thin, say so in notes and use the strongest available detail.
4. Middle: one-sentence value prop tied to their role/pain, not a product dump.
5. Close: one specific, low-friction ask (15-minute call, a reply with yes/no, a link they can glance at). Never "let me know if you're interested."
6. Voice: direct, plain English, like a smart peer. No "I hope this finds you well." No "Just circling back." No superlatives ("amazing," "world-class"). No "synergy."
7. Sign-off matches the sender's first name.
8. Do not fabricate shared connections, prior meetings, or facts not in the inputs.

Output JSON only:
{
  "subject_lines": ["...", "...", "..."],
  "email_body": "Hi [Name],\\n\\n...\\n\\nBest,\\n[Sender]",
  "personalization_hook": "the specific detail you anchored the opener on",
  "notes": "one sentence on what you leaned into and what to tweak if reply rates are soft"
}

No preamble, no trailing commentary — JSON only."""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/personalize", methods=["POST"])
def personalize():
    data = request.get_json(silent=True) or {}
    recipient = (data.get("recipient") or "").strip()
    pitch = (data.get("pitch") or "").strip()
    sender_name = (data.get("sender_name") or "").strip()

    if not recipient or not pitch or not sender_name:
        return jsonify({"error": "recipient, pitch, and sender_name are all required."}), 400

    if len(recipient) > 8000 or len(pitch) > 4000:
        return jsonify({"error": "Recipient profile max 8000 chars; pitch max 4000 chars."}), 400

    user_message = (
        f"<recipient_profile>\n{recipient}\n</recipient_profile>\n\n"
        f"<sender_pitch>\n{pitch}\n</sender_pitch>\n\n"
        f"<sender_name>{sender_name}</sender_name>\n\n"
        "Write one personalized cold email plus three subject lines. Return JSON only."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1536,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
    except anthropic.APIStatusError as e:
        return jsonify({"error": f"Upstream error: {e.message}"}), 502
    except anthropic.APIConnectionError:
        return jsonify({"error": "Could not reach Claude. Try again."}), 503

    text = next((b.text for b in response.content if b.type == "text"), "")

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return jsonify({"error": "Model returned non-JSON output.", "raw": text}), 500

    return jsonify(
        {
            "subject_lines": parsed.get("subject_lines", []),
            "email_body": parsed.get("email_body", ""),
            "personalization_hook": parsed.get("personalization_hook", ""),
            "notes": parsed.get("notes", ""),
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
                "cache_creation_input_tokens": getattr(
                    response.usage, "cache_creation_input_tokens", 0
                ),
            },
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
