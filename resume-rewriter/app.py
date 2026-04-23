import json
import os

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

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
7. Cut filler: "successfully", "various", "a variety of", "utilized", "leveraged synergies".

Output format: respond with JSON only, matching this schema exactly:
{
  "bullets": ["bullet 1", "bullet 2", ...],
  "keywords_matched": ["keyword from JD that appears in bullets", ...],
  "notes": "one or two sentences on what you prioritized and what the candidate should verify or strengthen"
}

No preamble, no trailing commentary — JSON only."""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/rewrite", methods=["POST"])
def rewrite():
    data = request.get_json(silent=True) or {}
    job_description = (data.get("job_description") or "").strip()
    experience = (data.get("experience") or "").strip()

    if not job_description or not experience:
        return jsonify({"error": "Both job_description and experience are required."}), 400

    if len(job_description) > 15000 or len(experience) > 15000:
        return jsonify({"error": "Inputs exceed 15,000 characters each."}), 400

    user_message = (
        f"<job_description>\n{job_description}\n</job_description>\n\n"
        f"<candidate_experience>\n{experience}\n</candidate_experience>\n\n"
        "Rewrite the candidate's experience as 5-8 tailored bullets for this role. Return JSON only."
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
            "bullets": parsed.get("bullets", []),
            "keywords_matched": parsed.get("keywords_matched", []),
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
