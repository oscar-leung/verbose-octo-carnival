import json
import os

import anthropic
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

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
8. Do not invent experience, certifications, classifications, or past employers. Reframing is fine; inventing is not.

Output JSON only, matching this schema:
{
  "responses": [
    {
      "prompt": "the prompt this response addresses (verbatim)",
      "response": "the SOQ response text",
      "structure": "STAR" or "CAR",
      "keywords_matched": ["phrases from the posting that appear in the response", ...]
    },
    ...
  ],
  "notes": "one paragraph on what you prioritized, which MQ/DQ items are strongly covered, and what the candidate should verify (especially any (approximate) numbers) or strengthen before submitting"
}

No preamble, no trailing commentary — JSON only."""


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    prompts_raw = (data.get("prompts") or "").strip()
    experience = (data.get("experience") or "").strip()
    duty_statement = (data.get("duty_statement") or "").strip()

    if not prompts_raw or not experience:
        return jsonify({"error": "Both prompts and experience are required."}), 400

    if len(prompts_raw) > 10000 or len(experience) > 20000 or len(duty_statement) > 20000:
        return jsonify({"error": "Input size limit exceeded."}), 400

    user_message_parts = [
        f"<soq_prompts>\n{prompts_raw}\n</soq_prompts>",
    ]
    if duty_statement:
        user_message_parts.append(
            f"<duty_statement_and_qualifications>\n{duty_statement}\n</duty_statement_and_qualifications>"
        )
    user_message_parts.append(f"<candidate_experience>\n{experience}\n</candidate_experience>")
    user_message_parts.append(
        "Produce one STAR/CAR response per SOQ prompt above. Mirror the posting's language. "
        "Return JSON only."
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
            "responses": parsed.get("responses", []),
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
    port = int(os.environ.get("PORT", 5002))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
