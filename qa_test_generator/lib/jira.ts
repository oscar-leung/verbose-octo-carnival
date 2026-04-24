export type JiraCreds = {
  /** e.g. "mycompany" → "https://mycompany.atlassian.net" */
  domain: string;
  email: string;
  apiToken: string;
  projectKey: string;
  issueType: string;
};

export type JiraTestCaseInput = {
  id: string;
  title: string;
  category: string;
  priority: string;
  preconditions: string[];
  steps: string[];
  expected_result: string;
};

export type JiraPushResult = {
  id: string;
  key?: string;
  url?: string;
  error?: string;
};

function baseUrl(domain: string): string {
  // Accept full URL, hostname, or subdomain.
  let d = domain.trim().replace(/^https?:\/\//, "").replace(/\/+$/, "");
  if (!d.includes(".")) d = `${d}.atlassian.net`;
  return `https://${d}`;
}

function authHeader(email: string, apiToken: string): string {
  const b64 = Buffer.from(`${email}:${apiToken}`).toString("base64");
  return `Basic ${b64}`;
}

/**
 * Build Atlassian Document Format (ADF) for the issue description.
 * Jira Cloud v3 REST API requires ADF for the description field.
 */
function buildDescriptionAdf(tc: JiraTestCaseInput): object {
  const nodes: object[] = [];

  nodes.push({
    type: "paragraph",
    content: [
      { type: "text", text: "Category: ", marks: [{ type: "strong" }] },
      { type: "text", text: tc.category },
      { type: "hardBreak" },
      { type: "text", text: "Priority: ", marks: [{ type: "strong" }] },
      { type: "text", text: tc.priority },
      { type: "hardBreak" },
      { type: "text", text: "Source: ", marks: [{ type: "strong" }] },
      { type: "text", text: `qa-test-generator · ${tc.id}` },
    ],
  });

  if (tc.preconditions.length > 0) {
    nodes.push({
      type: "heading",
      attrs: { level: 3 },
      content: [{ type: "text", text: "Preconditions" }],
    });
    nodes.push({
      type: "bulletList",
      content: tc.preconditions.map((p) => ({
        type: "listItem",
        content: [{ type: "paragraph", content: [{ type: "text", text: p }] }],
      })),
    });
  }

  nodes.push({
    type: "heading",
    attrs: { level: 3 },
    content: [{ type: "text", text: "Steps" }],
  });
  nodes.push({
    type: "orderedList",
    content: tc.steps.map((s) => ({
      type: "listItem",
      content: [{ type: "paragraph", content: [{ type: "text", text: s }] }],
    })),
  });

  nodes.push({
    type: "heading",
    attrs: { level: 3 },
    content: [{ type: "text", text: "Expected Result" }],
  });
  nodes.push({
    type: "paragraph",
    content: [{ type: "text", text: tc.expected_result }],
  });

  return { type: "doc", version: 1, content: nodes };
}

export async function pushTestCaseToJira(
  creds: JiraCreds,
  tc: JiraTestCaseInput,
): Promise<JiraPushResult> {
  const url = `${baseUrl(creds.domain)}/rest/api/3/issue`;
  const body = {
    fields: {
      project: { key: creds.projectKey },
      summary: tc.title.slice(0, 254),
      issuetype: { name: creds.issueType || "Test" },
      description: buildDescriptionAdf(tc),
      labels: [
        `qa-generated`,
        `cat-${tc.category.replace(/_/g, "-")}`,
        `prio-${tc.priority}`,
        `src-${tc.id}`,
      ],
    },
  };

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: authHeader(creds.email, creds.apiToken),
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      let detail = "";
      try {
        const j = (await res.json()) as { errorMessages?: string[]; errors?: object };
        detail =
          (j.errorMessages?.join("; ") ?? "") +
          (j.errors ? ` ${JSON.stringify(j.errors)}` : "");
      } catch {
        try {
          detail = (await res.text()).slice(0, 300);
        } catch {
          // ignore
        }
      }
      return {
        id: tc.id,
        error: `Jira returned ${res.status}${detail ? `: ${detail}` : ""}`,
      };
    }
    const created = (await res.json()) as { id?: string; key?: string };
    if (!created.key) {
      return { id: tc.id, error: "Jira returned no issue key." };
    }
    return {
      id: tc.id,
      key: created.key,
      url: `${baseUrl(creds.domain)}/browse/${created.key}`,
    };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    return { id: tc.id, error: message };
  }
}
