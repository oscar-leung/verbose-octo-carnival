import Anthropic from "@anthropic-ai/sdk";
import { NextRequest, NextResponse } from "next/server";
import { getOrCreateUserId } from "@/lib/session";
import { consumeQuota } from "@/lib/rate-limit";

export const runtime = "nodejs";
export const maxDuration = 120;

const ALLOWED_MIME = ["image/png", "image/jpeg", "image/webp", "image/gif"] as const;
type AllowedMime = (typeof ALLOWED_MIME)[number];
const MAX_SCREENSHOTS = 6;
const MAX_IMAGE_BYTES = 5 * 1024 * 1024; // 5MB per image (post-resize on client)

type Screenshot = { mediaType: AllowedMime; data: string };

const TEST_CASE_SCHEMA = {
  type: "object",
  properties: {
    feature_summary: {
      type: "string",
      description:
        "One- to two-sentence summary of the feature under test, synthesized from text and any screenshots provided.",
    },
    test_cases: {
      type: "array",
      description: "Comprehensive test cases. Aim for 8-25 depending on feature complexity.",
      items: {
        type: "object",
        properties: {
          id: { type: "string", description: "Stable identifier like TC-001." },
          title: { type: "string", description: "Short, action-oriented title." },
          category: {
            type: "string",
            enum: [
              "happy_path",
              "edge_case",
              "negative",
              "boundary",
              "security",
              "performance",
              "accessibility",
            ],
          },
          priority: { type: "string", enum: ["high", "medium", "low"] },
          preconditions: {
            type: "array",
            items: { type: "string" },
            description: "State that must hold before the test starts.",
          },
          steps: {
            type: "array",
            items: { type: "string" },
            description: "Numbered actions a tester or automation performs.",
          },
          expected_result: {
            type: "string",
            description: "Observable outcome that defines pass/fail.",
          },
        },
        required: [
          "id",
          "title",
          "category",
          "priority",
          "preconditions",
          "steps",
          "expected_result",
        ],
        additionalProperties: false,
      },
    },
  },
  required: ["feature_summary", "test_cases"],
  additionalProperties: false,
} as const;

const SYSTEM_PROMPT = `You are a senior SDET generating production-grade test cases for an app or website.

Inputs may include any combination of:
- A written feature description.
- Screenshots of the actual UI (mobile, tablet, or desktop). When screenshots are present, ground the test cases in what is actually visible: button labels, field names, error states, navigation, and observable affordances. Do NOT hallucinate UI elements that are not in the screenshots.

Coverage requirements:
- At least one happy path test for each primary user flow you can identify.
- Edge cases (empty values, max lengths, unicode, concurrency, time-zone, locale).
- Negative tests for invalid input, unauthorized access, and rate-limit triggers.
- Boundary tests where numeric or temporal limits exist.
- Security tests when authentication, authorization, secrets, or PII appear.
- Accessibility tests for any user-facing UI (keyboard nav, screen reader labels, color contrast, touch target size).

Style:
- Each test must be independently executable.
- Steps are imperative ("Tap 'Sign in'", "Enter 'foo@bar.com' in the Email field") - no narration.
- Reference exact UI labels you can see in screenshots, in quotes.
- Expected result is a single observable outcome.
- IDs are stable and zero-padded (TC-001, TC-002, ...).
- Skip categories that don't apply; do not invent UI tests for a backend-only feature, and do not invent backend tests for a pure UI screen.`;

function isAllowedMime(s: string): s is AllowedMime {
  return (ALLOWED_MIME as readonly string[]).includes(s);
}

function validateScreenshots(input: unknown): Screenshot[] | { error: string } {
  if (input === undefined || input === null) return [];
  if (!Array.isArray(input)) return { error: "screenshots must be an array." };
  if (input.length > MAX_SCREENSHOTS) {
    return { error: `Up to ${MAX_SCREENSHOTS} screenshots per request.` };
  }
  const out: Screenshot[] = [];
  for (const [i, raw] of input.entries()) {
    if (!raw || typeof raw !== "object") {
      return { error: `screenshots[${i}] must be an object.` };
    }
    const obj = raw as Record<string, unknown>;
    const mediaType = obj.mediaType;
    const data = obj.data;
    if (typeof mediaType !== "string" || !isAllowedMime(mediaType)) {
      return {
        error: `screenshots[${i}].mediaType must be one of ${ALLOWED_MIME.join(", ")}.`,
      };
    }
    if (typeof data !== "string" || data.length === 0) {
      return { error: `screenshots[${i}].data must be a non-empty base64 string.` };
    }
    // base64 length * 3/4 ≈ raw bytes
    const approxBytes = Math.floor((data.length * 3) / 4);
    if (approxBytes > MAX_IMAGE_BYTES) {
      return {
        error: `screenshots[${i}] is ~${Math.round(
          approxBytes / 1024 / 1024,
        )}MB. Resize to under ${MAX_IMAGE_BYTES / 1024 / 1024}MB and retry.`,
      };
    }
    out.push({ mediaType, data });
  }
  return out;
}

export async function POST(req: NextRequest) {
  let feature: string;
  let screenshotsInput: unknown;
  try {
    const body = await req.json();
    feature = typeof body?.feature === "string" ? body.feature.trim() : "";
    screenshotsInput = body?.screenshots;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const screenshotsResult = validateScreenshots(screenshotsInput);
  if ("error" in screenshotsResult) {
    return NextResponse.json({ error: screenshotsResult.error }, { status: 400 });
  }
  const screenshots: Screenshot[] = screenshotsResult;

  if (feature.length === 0 && screenshots.length === 0) {
    return NextResponse.json(
      { error: "Provide a feature description, screenshots, or both." },
      { status: 400 },
    );
  }
  if (feature.length > 20000) {
    return NextResponse.json(
      { error: "Feature description is too long (max 20,000 characters)." },
      { status: 400 },
    );
  }
  if (feature.length > 0 && feature.length < 5 && screenshots.length === 0) {
    return NextResponse.json(
      { error: "Provide either screenshots or a feature description of at least 5 characters." },
      { status: 400 },
    );
  }

  if (!process.env.ANTHROPIC_API_KEY) {
    return NextResponse.json(
      { error: "Server is missing ANTHROPIC_API_KEY." },
      { status: 500 },
    );
  }

  const { id: userId } = getOrCreateUserId();
  const { allowed, status } = await consumeQuota(userId);

  if (!allowed) {
    return NextResponse.json(
      {
        error:
          "Daily free-tier limit reached. Upgrade for unlimited generations, or try again after midnight UTC.",
        quota: status,
      },
      { status: 402 },
    );
  }

  const userContent: Anthropic.ContentBlockParam[] = [];
  for (const s of screenshots) {
    userContent.push({
      type: "image",
      source: { type: "base64", media_type: s.mediaType, data: s.data },
    });
  }
  const promptParts: string[] = [];
  if (screenshots.length > 0) {
    promptParts.push(
      `Above are ${screenshots.length} screenshot${
        screenshots.length === 1 ? "" : "s"
      } of the feature/app under test.`,
    );
  }
  if (feature.length > 0) {
    promptParts.push(`Feature description:\n\n<feature>\n${feature}\n</feature>`);
  }
  promptParts.push(
    "Generate the test cases. Return JSON matching the provided schema.",
  );
  userContent.push({ type: "text", text: promptParts.join("\n\n") });

  const client = new Anthropic();

  try {
    const response = await client.messages.create({
      model: "claude-opus-4-7",
      max_tokens: 16000,
      thinking: { type: "adaptive" },
      output_config: {
        effort: "high",
        format: { type: "json_schema", schema: TEST_CASE_SCHEMA },
      },
      system: SYSTEM_PROMPT,
      messages: [{ role: "user", content: userContent }],
    });

    const textBlock = response.content.find((b) => b.type === "text");
    if (!textBlock || textBlock.type !== "text") {
      return NextResponse.json({ error: "Empty response from model." }, { status: 502 });
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(textBlock.text);
    } catch {
      return NextResponse.json(
        { error: "Model returned non-JSON output." },
        { status: 502 },
      );
    }

    return NextResponse.json({ ...(parsed as object), quota: status });
  } catch (err) {
    if (err instanceof Anthropic.RateLimitError) {
      return NextResponse.json(
        { error: "Rate limited. Please retry in a moment.", quota: status },
        { status: 429 },
      );
    }
    if (err instanceof Anthropic.APIError) {
      return NextResponse.json(
        { error: `Upstream error (${err.status}): ${err.message}`, quota: status },
        { status: 502 },
      );
    }
    const message = err instanceof Error ? err.message : "Unknown error";
    return NextResponse.json({ error: message, quota: status }, { status: 500 });
  }
}
