import Anthropic from "@anthropic-ai/sdk";
import { NextRequest, NextResponse } from "next/server";
import { getOrCreateUserId } from "@/lib/session";
import { consumeQuota } from "@/lib/rate-limit";

export const runtime = "nodejs";
export const maxDuration = 120;

const TEST_CASE_SCHEMA = {
  type: "object",
  properties: {
    feature_summary: {
      type: "string",
      description: "One-sentence summary of the feature under test.",
    },
    test_cases: {
      type: "array",
      description: "Comprehensive test cases. Aim for 8-20 depending on feature complexity.",
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

const SYSTEM_PROMPT = `You are a senior SDET generating production-grade test cases.

Coverage requirements:
- At least one happy path test for each primary user flow described.
- Edge cases (empty values, max lengths, unicode, concurrency, time-zone, locale).
- Negative tests for invalid input, unauthorized access, and rate-limit triggers.
- Boundary tests where numeric or temporal limits exist.
- Security tests when authentication, authorization, secrets, or PII appear.
- Accessibility tests when there is any user-facing UI.

Style:
- Each test must be independently executable.
- Steps are imperative ("Click X", "Submit Y") - no narration.
- Expected result is a single observable outcome.
- IDs are stable and zero-padded (TC-001, TC-002, ...).
- Skip categories that don't apply to the feature; do not invent UI tests for a backend-only feature.`;

export async function POST(req: NextRequest) {
  let feature: string;
  try {
    const body = await req.json();
    feature = typeof body?.feature === "string" ? body.feature.trim() : "";
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  if (feature.length < 10) {
    return NextResponse.json(
      { error: "Provide a feature description of at least 10 characters." },
      { status: 400 },
    );
  }
  if (feature.length > 20000) {
    return NextResponse.json(
      { error: "Feature description is too long (max 20,000 characters)." },
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
      messages: [
        {
          role: "user",
          content: `Generate test cases for the following feature description.\n\n<feature>\n${feature}\n</feature>`,
        },
      ],
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
