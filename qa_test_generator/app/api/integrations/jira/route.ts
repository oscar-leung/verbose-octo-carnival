import { NextRequest, NextResponse } from "next/server";
import {
  pushTestCaseToJira,
  type JiraCreds,
  type JiraTestCaseInput,
  type JiraPushResult,
} from "@/lib/jira";

export const runtime = "nodejs";
export const maxDuration = 120;

function validateCreds(input: unknown): JiraCreds | { error: string } {
  if (!input || typeof input !== "object") return { error: "creds missing." };
  const c = input as Record<string, unknown>;
  const domain = typeof c.domain === "string" ? c.domain.trim() : "";
  const email = typeof c.email === "string" ? c.email.trim() : "";
  const apiToken = typeof c.apiToken === "string" ? c.apiToken.trim() : "";
  const projectKey = typeof c.projectKey === "string" ? c.projectKey.trim() : "";
  const issueType =
    typeof c.issueType === "string" && c.issueType.trim().length > 0
      ? c.issueType.trim()
      : "Test";
  if (!domain) return { error: "creds.domain missing." };
  if (!email) return { error: "creds.email missing." };
  if (!apiToken) return { error: "creds.apiToken missing." };
  if (!projectKey) return { error: "creds.projectKey missing." };
  return { domain, email, apiToken, projectKey, issueType };
}

function validateTestCase(input: unknown): JiraTestCaseInput | null {
  if (!input || typeof input !== "object") return null;
  const tc = input as Record<string, unknown>;
  if (
    typeof tc.id !== "string" ||
    typeof tc.title !== "string" ||
    typeof tc.category !== "string" ||
    typeof tc.priority !== "string" ||
    !Array.isArray(tc.preconditions) ||
    !Array.isArray(tc.steps) ||
    typeof tc.expected_result !== "string"
  ) {
    return null;
  }
  return {
    id: tc.id,
    title: tc.title,
    category: tc.category,
    priority: tc.priority,
    preconditions: tc.preconditions.filter((p): p is string => typeof p === "string"),
    steps: tc.steps.filter((s): s is string => typeof s === "string"),
    expected_result: tc.expected_result,
  };
}

export async function POST(req: NextRequest) {
  let body: { creds?: unknown; testCases?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const credsResult = validateCreds(body.creds);
  if ("error" in credsResult) {
    return NextResponse.json({ error: credsResult.error }, { status: 400 });
  }
  const creds = credsResult;

  if (!Array.isArray(body.testCases) || body.testCases.length === 0) {
    return NextResponse.json({ error: "testCases must be a non-empty array." }, { status: 400 });
  }
  if (body.testCases.length > 50) {
    return NextResponse.json(
      { error: "Push up to 50 test cases at a time." },
      { status: 400 },
    );
  }

  const validTcs: JiraTestCaseInput[] = [];
  for (const [i, raw] of body.testCases.entries()) {
    const tc = validateTestCase(raw);
    if (!tc) {
      return NextResponse.json(
        { error: `testCases[${i}] is missing required fields.` },
        { status: 400 },
      );
    }
    validTcs.push(tc);
  }

  // Sequential to respect Jira's per-user rate limits and give per-case errors.
  const results: JiraPushResult[] = [];
  for (const tc of validTcs) {
    results.push(await pushTestCaseToJira(creds, tc));
  }

  const created = results.filter((r) => r.key).length;
  const failed = results.length - created;
  return NextResponse.json({ results, created, failed });
}
