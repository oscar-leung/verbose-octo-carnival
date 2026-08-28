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
logger = logging.getLogger("soq-generator")

app = Flask(__name__)
client = anthropic.Anthropic()

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """You write Statements of Qualifications (SOQs) and cover letters for California state government job applications on CalCareers. You understand how civil service hiring actually works: SOQs are often scored by panel against a rubric tied to the exact bullets in the Duty Statement and the Minimum Qualifications / Desirable Qualifications sections. Applications that don't mirror the posting's language lose points even when the underlying experience is strong.

Your job: given one or more SOQ prompts (or a duty statement) and the candidate's experience, produce a structured response for each prompt.

Rules for every response:
1. One response per prompt. If the user provides N prompts, return N responses in order.
2. Length: 1/2 to 1 page per prompt unless the posting specifies otherwise. Default to ~350-500 words per prompt.
3. Structure each response in STAR or CAR format (Situation/Task, Action, Result — or Context, Action, Result). Lead with a one-sentence framing that restates the prompt in the candidate's words.
4. Mirror the posting's vocabulary. If the duty statement says "stakeholder engagement," "process improvement," "data analysis," or names a specific system (FI$Cal, CalHR, BCP, SB 14), use those exact phrases where the candidate has matching experience.
5. Quantify every result — hours saved, dollars, % improvement, headcount supported, volume processed. If a number is implied but not stated, add it with "(approximate)" and flag it in notes.
6. Use first person, plain English, past tense. No jargon salad, no "I am a passionate and driven...", no "seeking an opportunity to..."
7. Civil service reviewers look for: direct hits on each MQ/DQ, demonstrated initiative, collaboration across divisions, outcome ownership. Surface these when the experience supports it.
8. Do not invent experience, certifications, classifications, or past employers. Reframing is fine; inventing is not."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "responses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "response": {"type": "string"},
                    "structure": {"type": "string", "enum": ["STAR", "CAR"]},
                    "keywords_matched": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["prompt", "response", "structure", "keywords_matched"],
                "additionalProperties": False,
            },
        },
        "notes": {"type": "string"},
    },
    "required": ["responses", "notes"],
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


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompts_raw = (data.get("prompts") or "").strip()
    experience = (data.get("experience") or "").strip()
    duty_statement = (data.get("duty_statement") or "").strip()
    unlock_key = request.headers.get("X-Unlock-Key", "").strip()

    if not prompts_raw or not experience:
        return jsonify({"error": "Both prompts and experience are required."}), 400

    if len(prompts_raw) > 10000 or len(experience) > 20000 or len(duty_statement) > 20000:
        return jsonify({"error": "Input size limit exceeded."}), 400

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

    user_message_parts = [
        f"<soq_prompts>\n{prompts_raw}\n</soq_prompts>",
    ]
    if duty_statement:
        user_message_parts.append(
            f"<duty_statement_and_qualifications>\n{duty_statement}\n</duty_statement_and_qualifications>"
        )
    user_message_parts.append(f"<candidate_experience>\n{experience}\n</candidate_experience>")
    user_message_parts.append(
        "Produce one STAR/CAR response per SOQ prompt above. Mirror the posting's language."
    )

    user_message = "\n\n".join(user_message_parts)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=8192,
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
            "responses": parsed.get("responses", []),
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
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
