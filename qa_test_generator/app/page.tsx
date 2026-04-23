"use client";

import { useState } from "react";

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

type GenerateResponse = {
  feature_summary: string;
  test_cases: TestCase[];
};

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

export default function Page() {
  const [feature, setFeature] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateResponse | null>(null);

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
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  function downloadJSON() {
    if (!result) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "test_cases.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function downloadCSV() {
    if (!result) return;
    const header = ["id", "title", "category", "priority", "preconditions", "steps", "expected_result"];
    const rows = result.test_cases.map((tc) => [
      tc.id,
      tc.title,
      tc.category,
      tc.priority,
      tc.preconditions.join(" | "),
      tc.steps.map((s, i) => `${i + 1}. ${s}`).join(" | "),
      tc.expected_result,
    ]);
    const escape = (v: string) => `"${v.replace(/"/g, '""')}"`;
    const csv = [header, ...rows].map((r) => r.map(escape).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "test_cases.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8">
        <h1 className="text-3xl font-semibold tracking-tight">QA Test Case Generator</h1>
        <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
          Paste a feature description. Get structured test cases covering happy paths, edge cases,
          negative scenarios, boundaries, security, and accessibility.
        </p>
      </header>

      <section className="space-y-3">
        <textarea
          value={feature}
          onChange={(e) => setFeature(e.target.value)}
          rows={8}
          placeholder="e.g. Users can reset their password by entering their email; we send a one-time link valid for 15 minutes. After 5 failed attempts, the account is locked for 30 minutes..."
          className="w-full rounded-lg border border-neutral-300 bg-white p-4 text-sm shadow-sm focus:border-neutral-900 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:focus:border-neutral-200"
        />
        <div className="flex items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={loading || feature.trim().length < 10}
            className="rounded-lg bg-neutral-900 px-4 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40 dark:bg-neutral-100 dark:text-neutral-900"
          >
            {loading ? "Generating…" : "Generate test cases"}
          </button>
          {result && (
            <>
              <button
                onClick={downloadCSV}
                className="rounded-lg border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-700"
              >
                Export CSV
              </button>
              <button
                onClick={downloadJSON}
                className="rounded-lg border border-neutral-300 px-3 py-2 text-sm dark:border-neutral-700"
              >
                Export JSON
              </button>
            </>
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
