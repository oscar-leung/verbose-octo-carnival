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
logger = logging.getLogger("resume-rewriter")

app = Flask(__name__)
client = anthropic.Anthropic()

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT = """You are an elite resume bullet writer who has read thousands of job descriptions and coached senior engineers, PMs, designers, and analysts into top-tier companies.

Your one job: given a job description and a candidate's raw experience, rewrite the experience as 5 to 8 tailored resume bullets that will maximize the candidate's chance of landing an interview.

Rules for every bullet you write:
1. Start with a strong past-tense action verb (Led, Shipped, Architected, Automated, Reduced, Grew, Owned, Launched). Never "Responsible for" or "Helped with".
2. Quantify. Use real numbers from the candidate's experience whenever they exist (%, $, time saved, scale, team size, throughput). If a number is missing but clearly implied, make a conservative estimate and mark it with a trailing "(est.)" so the candidate knows to verify.
3. Mirror the job description's vocabulary and priorities. If the JD emphasizes "distributed systems," use that phrase. If it mentions specific tools (Kafka, Airflow, Figma, SQL, Salesforce), surface the candidate's matching experience using those exact words.
4. Structure: [Action verb] + [what you did, with technical specifics] + [measurable outcome or business impact]. Keep each bullet to one line, ideally 18-28 words.
5. Lead with the bullets that map most directly to the JD's top 2-3 requirements.
6. Do not fabricate experience, companies, titles, or technologies the candidate did not claim. You can reframe, not invent.
7. Cut filler: "successfully", "various", "a variety of", "utilized", "leveraged synergies"."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "bullets": {
            "type": "array",
            "items": {"type": "string"},
        },
        "keywords_matched": {
            "type": "array",
            "items": {"type": "string"},
        },
        "notes": {"type": "string"},
    },
    "required": ["bullets", "keywords_matched", "notes"],
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


@app.route("/api/rewrite", methods=["POST"])
def rewrite():
    data = request.get_json(silent=True) or {}
    job_description = (data.get("job_description") or "").strip()
    experience = (data.get("experience") or "").strip()
    unlock_key = request.headers.get("X-Unlock-Key", "").strip()

    if not job_description or not experience:
        return jsonify({"error": "Both job_description and experience are required."}), 400

    if len(job_description) > 15000 or len(experience) > 15000:
        return jsonify({"error": "Inputs exceed 15,000 characters each."}), 400

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
        f"<job_description>\n{job_description}\n</job_description>\n\n"
        f"<candidate_experience>\n{experience}\n</candidate_experience>\n\n"
        "Rewrite the candidate's experience as 5-8 tailored bullets for this role."
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
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
        logger.error("Non-JSON output from model: %r", text[:500])
        return jsonify({"error": "Model returned non-JSON output.", "raw": text}), 500

    return jsonify(
        {
            "bullets": parsed.get("bullets", []),
            "keywords_matched": parsed.get("keywords_matched", []),
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
