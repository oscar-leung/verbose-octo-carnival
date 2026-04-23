"use client";

import { useEffect, useState } from "react";

type Category =
  | "happy_path"
  | "edge_case"
  | "negative"
  | "boundary"
  | "security"
  | "performance"
  | "accessibility";

type Priority = "high" | "medium" | "low";

type TestCase = {
  id: string;
  title: string;
  category: Category;
  priority: Priority;
  preconditions: string[];
  steps: string[];
  expected_result: string;
};

type QuotaStatus = {
  subscribed: boolean;
  used: number;
  limit: number | "Infinity";
  remaining: number | "Infinity";
  resetAtIso: string;
};

type GenerateResponse = {
  feature_summary: string;
  test_cases: TestCase[];
  quota?: QuotaStatus;
};

type UsageResponse = QuotaStatus & { stripeConfigured: boolean };

type ExportFormat = "json" | "csv" | "jira" | "xray" | "testrail";

const CATEGORY_COLORS: Record<Category, string> = {
  happy_path: "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300",
  edge_case: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300",
  negative: "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300",
  boundary: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300",
  security: "bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-300",
  performance: "bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300",
  accessibility: "bg-pink-100 text-pink-800 dark:bg-pink-900/40 dark:text-pink-300",
};

const PRIORITY_COLORS: Record<Priority, string> = {
  high: "bg-red-500/20 text-red-700 dark:text-red-300",
  medium: "bg-amber-500/20 text-amber-700 dark:text-amber-300",
  low: "bg-neutral-500/20 text-neutral-700 dark:text-neutral-300",
};

const EXPORT_OPTIONS: { value: ExportFormat; label: string }[] = [
  { value: "csv", label: "Generic CSV" },
  { value: "json", label: "JSON" },
  { value: "jira", label: "Jira CSV" },
  { value: "xray", label: "Xray CSV (Jira app)" },
  { value: "testrail", label: "TestRail CSV" },
];

export default function Page() {
  const [feature, setFeature] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [upgrading, setUpgrading] = useState(false);

  async function refreshUsage() {
    try {
      const res = await fetch("/api/usage", { cache: "no-store" });
      if (res.ok) setUsage(await res.json());
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    refreshUsage();
  }, []);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feature }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Request failed");
      setResult(data);
      if (data.quota) setUsage((prev) => (prev ? { ...prev, ...data.quota } : data.quota));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      refreshUsage();
    } finally {
      setLoading(false);
    }
  }

  async function handleUpgrade() {
    setUpgrading(true);
    try {
      const res = await fetch("/api/checkout", { method: "POST" });
      const data = await res.json();
      if (!res.ok || !data.url) throw new Error(data.error ?? "Could not start checkout.");
      window.location.href = data.url as string;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not start checkout");
      setUpgrading(false);
    }
  }

  function downloadAs(format: ExportFormat) {
    if (!result) return;
    const { content, filename, mime } = buildExportClientSide(result, format);
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  const quotaLabel = (() => {
    if (!usage) return null;
    if (usage.subscribed) return "Unlimited · Pro";
    const remaining = typeof usage.remaining === "number" ? usage.remaining : 0;
    const limit = typeof usage.limit === "number" ? usage.limit : 0;
    return `${remaining}/${limit} free generations left today`;
  })();

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">QA Test Case Generator</h1>
          <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
            Paste a feature description. Get structured test cases covering happy paths, edge cases,
            negative scenarios, boundaries, security, and accessibility.
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          {quotaLabel && (
            <span className="rounded-full bg-neutral-200 px-3 py-1 text-xs font-medium dark:bg-neutral-800">
              {quotaLabel}
            </span>
          )}
          {usage && !usage.subscribed && usage.stripeConfigured && (
            <button
              onClick={handleUpgrade}
              disabled={upgrading}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              {upgrading ? "Redirecting…" : "Upgrade to Pro"}
            </button>
          )}
        </div>
      </header>

      <section className="space-y-3">
        <textarea
          value={feature}
          onChange={(e) => setFeature(e.target.value)}
          rows={8}
          placeholder="e.g. Users can reset their password by entering their email; we send a one-time link valid for 15 minutes. After 5 failed attempts, the account is locked for 30 minutes..."
          className="w-full rounded-lg border border-neutral-300 bg-white p-4 text-sm shadow-sm focus:border-neutral-900 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:focus:border-neutral-200"
        />
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={loading || feature.trim().length < 10}
            className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40 dark:bg-neutral-100 dark:text-neutral-900"
          >
            {loading ? "Generating…" : "Generate test cases"}
          </button>
          {result && (
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-neutral-500">Export as:</span>
              {EXPORT_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => downloadAs(opt.value)}
                  className="rounded-md border border-neutral-300 px-2.5 py-1 text-xs hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>
        {error && (
          <p className="rounded-md bg-red-100 px-3 py-2 text-sm text-red-800 dark:bg-red-900/40 dark:text-red-300">
            {error}
          </p>
        )}
      </section>

      {result && (
        <section className="mt-10 space-y-6">
          <div className="rounded-lg border border-neutral-200 bg-white p-4 text-sm dark:border-neutral-800 dark:bg-neutral-900">
            <h2 className="font-medium">Feature summary</h2>
            <p className="mt-1 text-neutral-700 dark:text-neutral-300">{result.feature_summary}</p>
          </div>

          <div className="space-y-3">
            <h2 className="text-lg font-medium">
              {result.test_cases.length} test case{result.test_cases.length === 1 ? "" : "s"}
            </h2>
            <ul className="space-y-3">
              {result.test_cases.map((tc) => (
                <li
                  key={tc.id}
                  className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-xs font-mono text-neutral-500">{tc.id}</div>
                      <div className="font-medium">{tc.title}</div>
                    </div>
                    <div className="flex shrink-0 gap-2">
                      <span className={`rounded px-2 py-0.5 text-xs ${CATEGORY_COLORS[tc.category]}`}>
                        {tc.category.replace("_", " ")}
                      </span>
                      <span className={`rounded px-2 py-0.5 text-xs ${PRIORITY_COLORS[tc.priority]}`}>
                        {tc.priority}
                      </span>
                    </div>
                  </div>

                  {tc.preconditions.length > 0 && (
                    <div className="mt-3">
                      <div className="text-xs font-semibold uppercase text-neutral-500">
                        Preconditions
                      </div>
                      <ul className="mt-1 list-disc pl-5 text-sm">
                        {tc.preconditions.map((p, i) => (
                          <li key={i}>{p}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  <div className="mt-3">
                    <div className="text-xs font-semibold uppercase text-neutral-500">Steps</div>
                    <ol className="mt-1 list-decimal pl-5 text-sm">
                      {tc.steps.map((s, i) => (
                        <li key={i}>{s}</li>
                      ))}
                    </ol>
                  </div>

                  <div className="mt-3">
                    <div className="text-xs font-semibold uppercase text-neutral-500">
                      Expected result
                    </div>
                    <p className="mt-1 text-sm">{tc.expected_result}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </main>
  );
}

// Client-side rebuild of the exporters so we don't round-trip large payloads.
function buildExportClientSide(
  result: GenerateResponse,
  format: ExportFormat,
): { content: string; filename: string; mime: string } {
  const escape = (v: string) => `"${String(v).replace(/"/g, '""')}"`;
  const toCsv = (rows: string[][]) => rows.map((r) => r.map(escape).join(",")).join("\r\n");
  const prioLabel: Record<Priority, string> = { high: "High", medium: "Medium", low: "Low" };

  if (format === "json") {
    return {
      content: JSON.stringify(result, null, 2),
      filename: "test_cases.json",
      mime: "application/json",
    };
  }

  if (format === "csv") {
    const rows = [
      ["id", "title", "category", "priority", "preconditions", "steps", "expected_result"],
      ...result.test_cases.map((tc) => [
        tc.id,
        tc.title,
        tc.category,
        tc.priority,
        tc.preconditions.join(" | "),
        tc.steps.map((s, i) => `${i + 1}. ${s}`).join(" | "),
        tc.expected_result,
      ]),
    ];
    return { content: toCsv(rows), filename: "test_cases.csv", mime: "text/csv" };
  }

  if (format === "jira") {
    const rows = [
      ["Summary", "Issue Type", "Priority", "Labels", "Description"],
      ...result.test_cases.map((tc) => {
        const desc = [
          `*Category:* ${tc.category}`,
          tc.preconditions.length
            ? `*Preconditions:*\n${tc.preconditions.map((p) => `- ${p}`).join("\n")}`
            : "",
          `*Steps:*\n${tc.steps.map((s) => `# ${s}`).join("\n")}`,
          `*Expected Result:*\n${tc.expected_result}`,
        ]
          .filter(Boolean)
          .join("\n\n");
        return [
          tc.title,
          "Test",
          prioLabel[tc.priority],
          `${tc.category} qa-generated id-${tc.id}`,
          desc,
        ];
      }),
    ];
    return { content: toCsv(rows), filename: "test_cases_jira.csv", mime: "text/csv" };
  }

  if (format === "xray") {
    const rows: string[][] = [
      ["TCID", "Summary", "Priority", "Labels", "Test Type", "Action", "Data", "Result"],
    ];
    for (const tc of result.test_cases) {
      const preconditions = tc.preconditions.join(" | ");
      if (tc.steps.length === 0) {
        rows.push([
          tc.id,
          tc.title,
          prioLabel[tc.priority],
          `${tc.category} qa-generated`,
          "Manual",
          "",
          preconditions,
          tc.expected_result,
        ]);
        continue;
      }
      tc.steps.forEach((step, i) => {
        rows.push([
          tc.id,
          i === 0 ? tc.title : "",
          i === 0 ? prioLabel[tc.priority] : "",
          i === 0 ? `${tc.category} qa-generated` : "",
          i === 0 ? "Manual" : "",
          step,
          i === 0 ? preconditions : "",
          i === tc.steps.length - 1 ? tc.expected_result : "",
        ]);
      });
    }
    return { content: toCsv(rows), filename: "test_cases_xray.csv", mime: "text/csv" };
  }

  // testrail
  const typeMap: Record<Category, string> = {
    happy_path: "Functional",
    edge_case: "Functional",
    negative: "Functional",
    boundary: "Functional",
    security: "Security",
    performance: "Performance",
    accessibility: "Accessibility",
  };
  const rows = [
    ["ID", "Title", "Section", "Priority", "Type", "Preconditions", "Steps", "Expected Result"],
    ...result.test_cases.map((tc) => [
      tc.id,
      tc.title,
      tc.category,
      prioLabel[tc.priority],
      typeMap[tc.category],
      tc.preconditions.join("\n"),
      tc.steps.map((s, i) => `${i + 1}. ${s}`).join("\n"),
      tc.expected_result,
    ]),
  ];
  return { content: toCsv(rows), filename: "test_cases_testrail.csv", mime: "text/csv" };
}
