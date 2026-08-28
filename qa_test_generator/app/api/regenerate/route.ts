import Anthropic from "@anthropic-ai/sdk";
import { NextRequest, NextResponse } from "next/server";
import { getOrCreateUserId } from "@/lib/session";
import { consumeQuota } from "@/lib/rate-limit";

export const runtime = "nodejs";
export const maxDuration = 120;

const ALLOWED_MIME = ["image/png", "image/jpeg", "image/webp", "image/gif"] as const;
type AllowedMime = (typeof ALLOWED_MIME)[number];
const MAX_SCREENSHOTS = 6;
const MAX_IMAGE_BYTES = 5 * 1024 * 1024;

type Screenshot = { mediaType: AllowedMime; data: string };

const CATEGORY_ENUM = [
  "happy_path",
  "edge_case",
  "negative",
  "boundary",
  "security",
  "performance",
  "accessibility",
] as const;

type TestCase = {
  id: string;
  title: string;
  category: (typeof CATEGORY_ENUM)[number];
  priority: "high" | "medium" | "low";
  preconditions: string[];
  steps: string[];
  expected_result: string;
};

const SINGLE_TEST_SCHEMA = {
  type: "object",
  properties: {
    id: { type: "string", description: "Stable identifier, preserved from the original." },
    title: {
      type: "string",
      description:
        "Describes the specific behavior being verified, NOT the category. Good: 'Blank email shows Required inline error'.",
    },
    category: { type: "string", enum: CATEGORY_ENUM },
    priority: {
      type: "string",
      enum: ["high", "medium", "low"],
      description:
        "high = blocks release, data loss / security risk, primary flow broken. medium = degraded UX, non-primary flow, edges affecting >1% of users. low = cosmetic, rare edges, polish.",
    },
    preconditions: {
      type: "array",
      items: { type: "string" },
      description: "Specific setup state with concrete test data.",
    },
    steps: {
      type: "array",
      items: { type: "string" },
      description: "Atomic imperative actions; one action per step; quote UI labels exactly.",
    },
    expected_result: {
      type: "string",
      description:
        "Single observable, specific outcome — exact text, exact status, exact UI state.",
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
} as const;

const SYSTEM_PROMPT = `You are a senior SDET refining a single test case based on user feedback. Someone is paying $9/month for this output — it must be good enough to paste into Jira or TestRail with zero manual rework.

You will receive:
- The original feature description and/or screenshots.
- The existing test case that needs refinement.
- Feedback on what is wrong or what should change.

Return a single revised test case following the user's feedback. Preserve the "id" field exactly. You may change any other field (title, category, priority, preconditions, steps, expected_result) if the feedback warrants it. Apply the same quality bar as the original generation:

<style_rules>
- Concrete test data, not placeholders. "not-an-email@" — not "an invalid email".
- Expected result is a single observable outcome with specifics: exact text, status code, UI state, response header.
- Atomic imperative steps; one action per step; verification belongs in expected_result, not in a step.
- Title describes the verified behavior, not the category.
- Preconditions specify concrete state including test data, not just roles.
- Reference UI labels in single quotes, exactly as shown in any screenshots.
</style_rules>

If the feedback is vague (e.g. "improve this"), apply the rubric above to whichever field is weakest — usually expected_result (add specificity) or preconditions (add concrete test data).`;

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
    const approxBytes = Math.floor((data.length * 3) / 4);
    if (approxBytes > MAX_IMAGE_BYTES) {
      return {
        error: `screenshots[${i}] is larger than ${MAX_IMAGE_BYTES / 1024 / 1024}MB.`,
      };
    }
    out.push({ mediaType, data });
  }
  return out;
}

function validateTestCase(input: unknown): TestCase | { error: string } {
  if (!input || typeof input !== "object") return { error: "testCase must be an object." };
  const tc = input as Record<string, unknown>;
  if (typeof tc.id !== "string" || tc.id.length === 0) return { error: "testCase.id missing." };
  if (typeof tc.title !== "string") return { error: "testCase.title missing." };
  if (
    typeof tc.category !== "string" ||
    !(CATEGORY_ENUM as readonly string[]).includes(tc.category)
  ) {
    return { error: "testCase.category invalid." };
  }
  if (typeof tc.priority !== "string" || !["high", "medium", "low"].includes(tc.priority)) {
    return { error: "testCase.priority invalid." };
  }
  if (!Array.isArray(tc.preconditions) || !tc.preconditions.every((p) => typeof p === "string")) {
    return { error: "testCase.preconditions must be string[]." };
  }
  if (!Array.isArray(tc.steps) || !tc.steps.every((s) => typeof s === "string")) {
    return { error: "testCase.steps must be string[]." };
  }
  if (typeof tc.expected_result !== "string") {
    return { error: "testCase.expected_result missing." };
  }
  return {
    id: tc.id,
    title: tc.title,
    category: tc.category as TestCase["category"],
    priority: tc.priority as TestCase["priority"],
    preconditions: tc.preconditions as string[],
    steps: tc.steps as string[],
    expected_result: tc.expected_result,
  };
}

export async function POST(req: NextRequest) {
  let body: Record<string, unknown>;
  try {
    body = (await req.json()) as Record<string, unknown>;
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const feature = typeof body.feature === "string" ? body.feature.trim() : "";
  const instruction = typeof body.instruction === "string" ? body.instruction.trim() : "";

  const screenshotsResult = validateScreenshots(body.screenshots);
  if ("error" in screenshotsResult) {
    return NextResponse.json({ error: screenshotsResult.error }, { status: 400 });
  }
  const screenshots: Screenshot[] = screenshotsResult;

  const tcResult = validateTestCase(body.testCase);
  if ("error" in tcResult) {
    return NextResponse.json({ error: tcResult.error }, { status: 400 });
  }
  const originalTc: TestCase = tcResult;

  if (feature.length === 0 && screenshots.length === 0) {
    return NextResponse.json(
      { error: "Need original feature description or screenshots to regenerate in context." },
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

  const parts: string[] = [];
  if (feature.length > 0) {
    parts.push(`<feature>\n${feature}\n</feature>`);
  }
  parts.push(
    `<existing_test_case>\n${JSON.stringify(originalTc, null, 2)}\n</existing_test_case>`,
  );
  parts.push(
    `<feedback>\n${instruction || "Improve this test case. Make the expected result more specific, the preconditions more concrete, and the steps more atomic."}\n</feedback>`,
  );
  parts.push(
    "Return the revised test case as a single JSON object matching the schema. Preserve the id exactly.",
  );
  userContent.push({ type: "text", text: parts.join("\n\n") });

  const client = new Anthropic();

  try {
    const response = await client.messages.create({
      model: "claude-opus-4-7",
      max_tokens: 4000,
      thinking: { type: "adaptive" },
      output_config: {
        effort: "max",
        format: { type: "json_schema", schema: SINGLE_TEST_SCHEMA },
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

    const validated = validateTestCase(parsed);
    if ("error" in validated) {
      return NextResponse.json(
        { error: `Model output failed schema validation: ${validated.error}` },
        { status: 502 },
      );
    }
    // Defensive: force the id back even if the model renamed it.
    validated.id = originalTc.id;

    return NextResponse.json({ testCase: validated, quota: status });
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
