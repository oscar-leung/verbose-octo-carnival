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
        "One to two sentences capturing the primary user-visible behavior, its trigger, and its major constraints (limits, auth, persistence). Specific, not marketing.",
    },
    test_cases: {
      type: "array",
      description:
        "Between 8 and 25 test cases. Simple one-flow features ~= 10; complex multi-step multi-role features ~= 20-25.",
      items: {
        type: "object",
        properties: {
          id: {
            type: "string",
            description: "Zero-padded stable identifier: TC-001, TC-002, ...",
          },
          title: {
            type: "string",
            description:
              "Describes the specific behavior being verified, NOT the category. Good: 'Blank email shows inline Required error'. Bad: 'Negative email test'.",
          },
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
          priority: {
            type: "string",
            enum: ["high", "medium", "low"],
            description:
              "high = blocks release, data loss / security risk, primary flow broken. medium = degraded UX, non-primary flow, edge cases affecting >1% of users. low = cosmetic, rare edges, polish.",
          },
          preconditions: {
            type: "array",
            items: { type: "string" },
            description:
              "Specific setup state, including concrete test data. Bad: 'user is logged in'. Good: \"Authenticated as user with email='primary+test@example.com', role='customer', failed_login_attempts_last_hour=0.\"",
          },
          steps: {
            type: "array",
            items: { type: "string" },
            description:
              "Atomic imperative actions; each step does one thing. Good: \"Click 'Sign in'\" / \"Enter 'bad@' in 'Email' field\". Bad: 'Click Sign in and verify error appears'. Quote UI labels exactly as they appear.",
          },
          expected_result: {
            type: "string",
            description:
              "Single observable, specific outcome — exact text, exact status code, exact UI state. Bad: 'Error is shown'. Good: \"Page displays exact text 'Please enter a valid email address' in red (#DC2626) below the Email input; Submit button is disabled.\"",
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

const SYSTEM_PROMPT = `You are a senior SDET generating paying-customer-quality test cases. Someone is paying $9/month for this output — it must be good enough to paste into Jira or TestRail with zero manual rework.

<inputs>
A written feature description, screenshots of the actual UI (mobile / tablet / desktop), or both.

When screenshots are present:
- Ground every test in what is actually visible: exact button labels, field names, error states, nav elements, affordances.
- Reference UI labels in single quotes, exactly as shown: 'Sign in', 'Continue with Google'.
- Do NOT invent UI elements that are not in the screenshots.
</inputs>

<coverage_rules>
Generate tests that cover these axes where the spec warrants them. Skip axes that don't apply — do not invent backend tests for a pure-UI screen or UI tests for a backend-only API.

1. Happy path: at least one per primary user flow you can identify.
2. For every user input field: at least one empty case, one invalid-format case, one boundary-overflow case (max + 1), and one valid-edge case (minimum allowed).
3. For every numeric or temporal limit mentioned in the spec: test at the limit, limit + 1, limit - 1, 0, and (where applicable) negative.
4. Authorization: unauthenticated, under-privileged role, expired session, logged-in-as-different-user.
5. Rate limits, timeouts, concurrency: if the spec mentions N req/min, test N (allowed), N+1 (rate-limited response shape + Retry-After header).
6. Security (free-text inputs): SQL injection ("' OR 1=1 --"), XSS ("<script>alert(1)</script>"). For state-changing requests: CSRF token missing/invalid. For PII: confirm it is never returned in error messages or logs.
7. Accessibility for any user-facing UI: keyboard-only navigation reaches every interactive element; all inputs have programmatic labels (aria-label / label 'for'); color contrast meets WCAG AA (4.5:1 for body text); touch targets >= 44×44 px.
8. Cross-environment where the spec implies it: mobile web vs desktop, supported browsers, localization.
</coverage_rules>

<test_data_rules>
Use concrete values, never placeholders.

Bad: "an invalid email"
Good: "'not-an-email@'", "'a@'", "' ' (single space)", "'a'.repeat(254) + '@x.com'"

When text input is accepted, include at least one test with unicode ("éñ中🔥"), one with an RTL string ("مرحبا"), and one with a long string (>= 1000 chars).
When numeric limits exist, include the exact boundary values described above.
</test_data_rules>

<style_rules>
- Each test is self-contained: its preconditions create the exact state required. No "after running TC-003".
- Preconditions specify test data, not just roles. "User exists with email='p@x.com', password='P@ssw0rd!', failed_attempts_last_hour=0" — not "user is logged in".
- Steps are atomic and imperative: one action per step, no narration, no verification embedded in a step. "Click 'Submit'" — not "Click 'Submit' and verify error appears".
- Quote UI labels exactly as shown in the spec or screenshots.
- Expected result is a single observable outcome with specifics: exact text, exact status code, exact UI state, exact response header, exact element color, exact disabled state.
- Title describes the verified behavior, never the category. "Blank email shows 'Required' inline error" — not "Negative test for email".
- IDs are zero-padded: TC-001, TC-002, TC-003...
</style_rules>

<priority_rubric>
high = blocks release, data loss or security risk, primary user flow broken.
medium = degraded UX, non-primary flow broken, edge cases affecting more than 1% of users.
low = cosmetic issues, rare edges, accessibility polish beyond WCAG AA.
</priority_rubric>

<target_count>
8 to 25 tests depending on feature complexity. Simple single-flow feature ≈ 10. Complex multi-step, multi-role, auth + payment + email feature ≈ 20-25. Err on the side of more boundary and negative tests rather than padding happy paths.
</target_count>`;

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
      // "max" effort: Opus-tier only (Opus 4.6+). For paid test cases, thoroughness >
      // latency — a slight overthinking risk beats skipping boundary / security tests.
      output_config: {
        effort: "max",
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
