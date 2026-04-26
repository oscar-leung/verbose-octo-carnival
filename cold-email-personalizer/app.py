import json
import logging
import os

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, url_for

import billing
import ratelimit
import store

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("cold-email")

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
8. Do not fabricate shared connections, prior meetings, or facts not in the inputs."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "subject_lines": {
            "type": "array",
            "items": {"type": "string"},
        },
        "email_body": {"type": "string"},
        "personalization_hook": {"type": "string"},
        "notes": {"type": "string"},
    },
    "required": ["subject_lines", "email_body", "personalization_hook", "notes"],
    "additionalProperties": False,
}


store.init_db()


def _client_ip() -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.remote_addr or "unknown"


@app.route("/")
def index():
    ip = _client_ip()
    return render_template(
        "index.html",
        free_remaining=ratelimit.remaining(ip),
        free_limit=ratelimit.FREE_DAILY_LIMIT,
        billing_enabled=billing.is_enabled(),
    )


@app.route("/unlocked")
def unlocked():
    session_id = request.args.get("session_id", "").strip()
    if not session_id:
        return redirect(url_for("index"))

    if not billing.is_enabled():
        return "Billing is not configured.", 503

    try:
        key = billing.issue_key_for_session(session_id)
    except Exception:
        logger.exception("Failed to issue unlock key for session %s", session_id)
        return "Could not verify your payment. Email support and include your Stripe receipt.", 500

    if not key:
        return "Payment not yet confirmed. Refresh this page in a few seconds.", 202

    return render_template("unlocked.html", unlock_key=key)


@app.route("/api/personalize", methods=["POST"])
def personalize():
    data = request.get_json(silent=True) or {}
    recipient = (data.get("recipient") or "").strip()
    pitch = (data.get("pitch") or "").strip()
    sender_name = (data.get("sender_name") or "").strip()
    unlock_key = request.headers.get("X-Unlock-Key", "").strip()

    if not recipient or not pitch or not sender_name:
        return jsonify({"error": "recipient, pitch, and sender_name are all required."}), 400

    if len(recipient) > 8000 or len(pitch) > 4000:
        return jsonify({"error": "Recipient profile max 8000 chars; pitch max 4000 chars."}), 400

    ip = _client_ip()
    has_unlock = store.is_key_active(unlock_key) if unlock_key else False

    if not has_unlock:
        allowed, remaining = ratelimit.check_and_record(ip)
        if not allowed:
            return (
                jsonify(
                    {
                        "error": "Free daily limit reached.",
                        "code": "rate_limited",
                        "upgrade_available": billing.is_enabled(),
                    }
                ),
                429,
            )
    else:
        remaining = None

    user_message = (
        f"<recipient_profile>\n{recipient}\n</recipient_profile>\n\n"
        f"<sender_pitch>\n{pitch}\n</sender_pitch>\n\n"
        f"<sender_name>{sender_name}</sender_name>\n\n"
        "Write one personalized cold email plus three subject lines."
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
            output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
        )
    except anthropic.APIStatusError as e:
        logger.exception("Anthropic API error")
        return jsonify({"error": f"Upstream error: {e.message}"}), 502
    except anthropic.APIConnectionError:
        return jsonify({"error": "Could not reach Claude. Try again."}), 503

    text = next((b.text for b in response.content if b.type == "text"), "")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Non-JSON output: %r", text[:500])
        return jsonify({"error": "Model returned non-JSON output.", "raw": text}), 500

    return jsonify(
        {
            "subject_lines": parsed.get("subject_lines", []),
            "email_body": parsed.get("email_body", ""),
            "personalization_hook": parsed.get("personalization_hook", ""),
            "notes": parsed.get("notes", ""),
            "unlocked": has_unlock,
            "free_remaining": remaining,
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


@app.route("/api/checkout", methods=["POST"])
def checkout():
    if not billing.is_enabled():
        return jsonify({"error": "Billing is not configured."}), 503

    base = request.host_url.rstrip("/")
    try:
        url = billing.create_checkout_session(
            success_url=base + url_for("unlocked"),
            cancel_url=base + url_for("index"),
        )
    except Exception:
        logger.exception("Failed to create Stripe checkout session")
        return jsonify({"error": "Could not start checkout."}), 500

    return jsonify({"checkout_url": url})


@app.route("/api/stripe/webhook", methods=["POST"])
def stripe_webhook():
    if not billing.is_enabled():
        return ("", 204)

    sig = request.headers.get("Stripe-Signature", "")
    payload = request.get_data()
    try:
        billing.handle_webhook(payload, sig)
    except Exception:
        logger.exception("Webhook handling failed")
        return ("bad signature", 400)
    return ("", 200)


@app.route("/api/unlock-check", methods=["POST"])
def unlock_check():
    data = request.get_json(silent=True) or {}
    key = (data.get("unlock_key") or "").strip()
    return jsonify({"active": store.is_key_active(key)})


@app.route("/healthz")
def healthz():
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
