"use client";

import { useCallback, useEffect, useRef, useState } from "react";

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

type AllowedMime = "image/png" | "image/jpeg" | "image/webp" | "image/gif";

type Screenshot = {
  id: string;
  name: string;
  mediaType: AllowedMime;
  base64: string; // raw base64 (no data URL prefix), POSTed to API
  previewUrl: string; // data: URL for <img>
  bytes: number;
};

const ALLOWED_MIME: AllowedMime[] = ["image/png", "image/jpeg", "image/webp", "image/gif"];
const MAX_SCREENSHOTS = 6;
const MAX_LONG_EDGE_PX = 2000;
const RESIZE_MIME: AllowedMime = "image/jpeg";
const RESIZE_QUALITY = 0.9;

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

const SAMPLE_FEATURES: { label: string; text: string }[] = [
  {
    label: "Password reset",
    text: `Users can reset their password from the login page by entering their email. We send a one-time reset link valid for 15 minutes. After 5 failed login attempts within an hour, the account is locked for 30 minutes and the user is notified by email. The reset page requires a new password of at least 12 characters including one uppercase letter, one number, and one symbol. Reset links expire after first use. Locked accounts still receive reset emails but clicking the link shows a "contact support" page.`,
  },
  {
    label: "Checkout + payment",
    text: `Users add items to a cart from any product page. The cart persists across sessions for 30 days. At checkout, users enter a shipping address, choose a shipping method (Standard $5 / Express $12 / Overnight $25), enter payment via credit card (Stripe) or PayPal, then confirm. Inventory is reserved for 15 minutes during checkout; if it expires, the user is returned to the cart. If payment fails, the user stays on the payment step with a specific error. On success we show an order confirmation page with a unique order ID and send a receipt email. Guest checkout is allowed; optional account creation on the confirmation page.`,
  },
  {
    label: "Profile photo upload",
    text: `Authenticated users can upload a profile photo up to 5 MB. Supported formats: PNG, JPEG, WebP. Upload shows percentage progress and allows cancel. On success the image is resized server-side to 512×512 and displayed in the header within 2 seconds. Files over 5 MB or in an unsupported format show a specific error. Anonymous users see a "sign in to upload" prompt. Existing photo is retained until the new upload succeeds. The feature is available on web, iOS, and Android.`,
  },
  {
    label: "Rate-limited API",
    text: `POST /api/messages accepts JSON body {text: string (1-2000 chars), recipient_id: string}. Authentication via Bearer token in the Authorization header. Rate limit: 60 requests per minute per authenticated user, returning 429 with a Retry-After header when exceeded. Returns 201 with {message_id, created_at} on success, 400 on invalid body shape, 401 on missing or invalid token, 403 if the token lacks the messages:write scope, 404 when recipient_id does not exist, 413 when the body exceeds the 2000 character limit. All responses include an X-Request-Id header.`,
  },
];

async function dataUrlToScreenshot(dataUrl: string, name: string): Promise<Screenshot> {
  const img = await new Promise<HTMLImageElement>((resolve, reject) => {
    const el = new Image();
    el.onload = () => resolve(el);
    el.onerror = () => reject(new Error("Failed to decode image."));
    el.src = dataUrl;
  });

  const longEdge = Math.max(img.naturalWidth, img.naturalHeight);
  const needsResize = longEdge > MAX_LONG_EDGE_PX;
  const scale = needsResize ? MAX_LONG_EDGE_PX / longEdge : 1;
  const targetW = Math.round(img.naturalWidth * scale);
  const targetH = Math.round(img.naturalHeight * scale);

  const canvas = document.createElement("canvas");
  canvas.width = targetW;
  canvas.height = targetH;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("Canvas 2D context unavailable.");
  ctx.drawImage(img, 0, 0, targetW, targetH);

  const outputDataUrl = canvas.toDataURL(RESIZE_MIME, RESIZE_QUALITY);
  const commaIdx = outputDataUrl.indexOf(",");
  const base64 = outputDataUrl.slice(commaIdx + 1);
  const bytes = Math.floor((base64.length * 3) / 4);

  return {
    id: crypto.randomUUID(),
    name,
    mediaType: RESIZE_MIME,
    base64,
    previewUrl: outputDataUrl,
    bytes,
  };
}

async function fileToScreenshot(file: File): Promise<Screenshot> {
  if (!ALLOWED_MIME.includes(file.type as AllowedMime)) {
    throw new Error(`Unsupported image type: ${file.type || "unknown"}`);
  }
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error ?? new Error("Failed to read file."));
    reader.readAsDataURL(file);
  });
  return dataUrlToScreenshot(dataUrl, file.name || "screenshot.jpg");
}

export default function Page() {
  const [feature, setFeature] = useState("");
  const [screenshots, setScreenshots] = useState<Screenshot[]>([]);
  const [loading, setLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [upgrading, setUpgrading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [urlViewport, setUrlViewport] = useState<"desktop" | "mobile">("desktop");
  const [capturingUrl, setCapturingUrl] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  // Snapshot of inputs at generate time so regenerate uses the original context
  // even if the user edits the textarea or screenshots afterward.
  const [generatedContext, setGeneratedContext] = useState<{
    feature: string;
    screenshots: Screenshot[];
  } | null>(null);
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
  const [feedbackDraftId, setFeedbackDraftId] = useState<string | null>(null);
  const [feedbackDraft, setFeedbackDraft] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState<TestCase | null>(null);

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

  const ingestFiles = useCallback(
    async (files: FileList | File[]) => {
      const list = Array.from(files).filter((f) =>
        ALLOWED_MIME.includes(f.type as AllowedMime),
      );
      if (list.length === 0) {
        setError("No supported images found (PNG, JPEG, WebP, or GIF).");
        return;
      }
      setError(null);
      setImporting(true);
      try {
        const remaining = MAX_SCREENSHOTS - screenshots.length;
        if (remaining <= 0) {
          setError(`Maximum ${MAX_SCREENSHOTS} screenshots reached.`);
          return;
        }
        const accepted = list.slice(0, remaining);
        const processed = await Promise.all(accepted.map(fileToScreenshot));
        setScreenshots((prev) => [...prev, ...processed]);
        if (list.length > accepted.length) {
          setError(
            `Only added ${accepted.length} of ${list.length} (max ${MAX_SCREENSHOTS} per request).`,
          );
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to process image.");
      } finally {
        setImporting(false);
      }
    },
    [screenshots.length],
  );

  async function captureUrl() {
    const url = urlInput.trim();
    if (!url) {
      setError("Enter a URL first.");
      return;
    }
    if (screenshots.length >= MAX_SCREENSHOTS) {
      setError(`Maximum ${MAX_SCREENSHOTS} screenshots reached.`);
      return;
    }
    setError(null);
    setCapturingUrl(true);
    try {
      const res = await fetch("/api/screenshot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, viewport: urlViewport }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Screenshot failed");
      const dataUrl = `data:${data.mediaType};base64,${data.base64}`;
      const hostname = (() => {
        try {
          return new URL(url).hostname;
        } catch {
          return "url-screenshot";
        }
      })();
      const shot = await dataUrlToScreenshot(
        dataUrl,
        `${hostname} (${urlViewport}).jpg`,
      );
      setScreenshots((prev) => [...prev, shot]);
      setUrlInput("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not capture URL");
    } finally {
      setCapturingUrl(false);
    }
  }

  // Paste-from-clipboard support: listen on document.
  useEffect(() => {
    function onPaste(e: ClipboardEvent) {
      if (!e.clipboardData) return;
      const files: File[] = [];
      for (const item of Array.from(e.clipboardData.items)) {
        if (item.kind === "file") {
          const f = item.getAsFile();
          if (f) files.push(f);
        }
      }
      if (files.length > 0) {
        e.preventDefault();
        void ingestFiles(files);
      }
    }
    document.addEventListener("paste", onPaste);
    return () => document.removeEventListener("paste", onPaste);
  }, [ingestFiles]);

  function removeScreenshot(id: string) {
    setScreenshots((prev) => prev.filter((s) => s.id !== id));
  }

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          feature,
          screenshots: screenshots.map((s) => ({
            mediaType: s.mediaType,
            data: s.base64,
          })),
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Request failed");
      setResult(data);
      setGeneratedContext({ feature, screenshots });
      if (data.quota) setUsage((prev) => (prev ? { ...prev, ...data.quota } : data.quota));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
      refreshUsage();
    } finally {
      setLoading(false);
    }
  }

  function startEdit(tc: TestCase) {
    setEditingId(tc.id);
    setEditDraft({ ...tc, preconditions: [...tc.preconditions], steps: [...tc.steps] });
    setFeedbackDraftId(null);
    setError(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditDraft(null);
  }

  function saveEdit() {
    if (!editDraft) return;
    const cleaned: TestCase = {
      ...editDraft,
      title: editDraft.title.trim(),
      expected_result: editDraft.expected_result.trim(),
      preconditions: editDraft.preconditions.map((p) => p.trim()).filter((p) => p.length > 0),
      steps: editDraft.steps.map((s) => s.trim()).filter((s) => s.length > 0),
    };
    setResult((prev) =>
      prev
        ? {
            ...prev,
            test_cases: prev.test_cases.map((tc) => (tc.id === cleaned.id ? cleaned : tc)),
          }
        : prev,
    );
    setEditingId(null);
    setEditDraft(null);
  }

  async function handleRegenerate(testCase: TestCase, instruction: string) {
    if (!generatedContext) return;
    setRegeneratingId(testCase.id);
    setError(null);
    try {
      const res = await fetch("/api/regenerate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          feature: generatedContext.feature,
          screenshots: generatedContext.screenshots.map((s) => ({
            mediaType: s.mediaType,
            data: s.base64,
          })),
          testCase,
          instruction,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? "Regenerate failed");
      if (data.testCase) {
        setResult((prev) =>
          prev
            ? {
                ...prev,
                test_cases: prev.test_cases.map((tc) =>
                  tc.id === testCase.id ? (data.testCase as TestCase) : tc,
                ),
              }
            : prev,
        );
      }
      if (data.quota) setUsage((prev) => (prev ? { ...prev, ...data.quota } : data.quota));
      setFeedbackDraftId(null);
      setFeedbackDraft("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not regenerate");
      refreshUsage();
    } finally {
      setRegeneratingId(null);
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

  const canGenerate =
    !loading && !importing && (feature.trim().length >= 5 || screenshots.length > 0);

  const totalImageMb = screenshots.reduce((acc, s) => acc + s.bytes, 0) / 1024 / 1024;

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Paste a feature spec.{" "}
            <span className="text-indigo-600 dark:text-indigo-400">Get 15+ test cases</span> in
            30 seconds.
          </h1>
          <p className="mt-3 text-sm text-neutral-600 dark:text-neutral-400">
            Happy paths, edge cases, negatives, boundaries, security, and accessibility.
            Exportable to Jira, Xray, TestRail, or plain CSV. Built for SDETs, QA leads, and
            devs shipping to prod without a dedicated QA team.
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

      <section className="space-y-4">
        <div>
          <div className="mb-1 flex flex-wrap items-center justify-between gap-2">
            <label className="text-xs font-semibold uppercase text-neutral-500">
              Feature description (optional if screenshots provided)
            </label>
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-xs text-neutral-500">Try a sample:</span>
              {SAMPLE_FEATURES.map((s) => (
                <button
                  key={s.label}
                  type="button"
                  onClick={() => {
                    setFeature(s.text);
                    setError(null);
                  }}
                  className="rounded-full border border-neutral-300 px-2.5 py-0.5 text-xs text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>
          <textarea
            value={feature}
            onChange={(e) => setFeature(e.target.value)}
            rows={6}
            placeholder="e.g. Users can reset their password by entering their email; we send a one-time link valid for 15 minutes..."
            className="w-full rounded-lg border border-neutral-300 bg-white p-4 text-sm shadow-sm focus:border-neutral-900 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:focus:border-neutral-200"
          />
        </div>

        <div>
          <label className="mb-1 block text-xs font-semibold uppercase text-neutral-500">
            Capture from URL (public pages only — no auth yet)
          </label>
          <div className="flex flex-wrap items-stretch gap-2">
            <input
              type="url"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !capturingUrl && urlInput.trim()) {
                  e.preventDefault();
                  void captureUrl();
                }
              }}
              placeholder="https://example.com/pricing"
              className="min-w-[240px] flex-1 rounded-lg border border-neutral-300 bg-white px-3 py-2 text-sm focus:border-neutral-900 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:focus:border-neutral-200"
            />
            <select
              value={urlViewport}
              onChange={(e) => setUrlViewport(e.target.value as "desktop" | "mobile")}
              className="rounded-lg border border-neutral-300 bg-white px-2 py-2 text-sm dark:border-neutral-700 dark:bg-neutral-900"
            >
              <option value="desktop">Desktop 1440×900</option>
              <option value="mobile">Mobile 390×844</option>
            </select>
            <button
              onClick={captureUrl}
              disabled={
                capturingUrl ||
                urlInput.trim().length === 0 ||
                screenshots.length >= MAX_SCREENSHOTS
              }
              className="rounded-lg bg-neutral-900 px-3 py-2 text-sm font-medium text-white disabled:cursor-not-allowed disabled:opacity-40 dark:bg-neutral-100 dark:text-neutral-900"
            >
              {capturingUrl ? "Capturing…" : "Capture"}
            </button>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-xs font-semibold uppercase text-neutral-500">
            Screenshots (drag & drop, click, or paste — up to {MAX_SCREENSHOTS})
          </label>
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              if (e.dataTransfer.files.length > 0) void ingestFiles(e.dataTransfer.files);
            }}
            onClick={() => fileInputRef.current?.click()}
            className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 text-sm transition-colors ${
              dragOver
                ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20"
                : "border-neutral-300 bg-white hover:bg-neutral-50 dark:border-neutral-700 dark:bg-neutral-900 dark:hover:bg-neutral-800"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={ALLOWED_MIME.join(",")}
              multiple
              hidden
              onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  void ingestFiles(e.target.files);
                }
                e.target.value = "";
              }}
            />
            <p className="text-neutral-700 dark:text-neutral-300">
              {importing ? "Processing…" : "Drag & drop, click, or ⌘V to paste"}
            </p>
            <p className="mt-1 text-xs text-neutral-500">
              PNG, JPEG, WebP, GIF · resized to {MAX_LONG_EDGE_PX}px on the long edge
            </p>
          </div>

          {screenshots.length > 0 && (
            <div className="mt-3">
              <div className="mb-2 flex items-center justify-between text-xs text-neutral-500">
                <span>
                  {screenshots.length} image{screenshots.length === 1 ? "" : "s"} ·{" "}
                  {totalImageMb.toFixed(2)} MB total
                </span>
                <button
                  onClick={() => setScreenshots([])}
                  className="text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100"
                >
                  Clear all
                </button>
              </div>
              <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                {screenshots.map((s) => (
                  <li
                    key={s.id}
                    className="group relative overflow-hidden rounded-lg border border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900"
                  >
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={s.previewUrl}
                      alt={s.name}
                      className="h-32 w-full object-cover"
                    />
                    <div className="px-2 py-1 text-xs">
                      <div className="truncate" title={s.name}>
                        {s.name}
                      </div>
                      <div className="text-neutral-500">{(s.bytes / 1024).toFixed(0)} KB</div>
                    </div>
                    <button
                      onClick={() => removeScreenshot(s.id)}
                      className="absolute right-1 top-1 rounded-full bg-black/60 px-2 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100"
                      aria-label={`Remove ${s.name}`}
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleGenerate}
            disabled={!canGenerate}
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
              {result.test_cases.map((tc) =>
                editingId === tc.id && editDraft ? (
                  <li
                    key={tc.id}
                    className="rounded-lg border border-indigo-300 bg-white p-4 dark:border-indigo-700 dark:bg-neutral-900"
                  >
                    <div className="mb-3 flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="text-xs font-mono text-neutral-500">{tc.id}</div>
                        <input
                          type="text"
                          value={editDraft.title}
                          onChange={(e) =>
                            setEditDraft({ ...editDraft, title: e.target.value })
                          }
                          className="mt-1 w-full rounded-md border border-neutral-300 bg-white px-2 py-1 text-sm font-medium focus:border-neutral-900 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:focus:border-neutral-200"
                        />
                      </div>
                      <div className="flex shrink-0 flex-col gap-2">
                        <select
                          value={editDraft.category}
                          onChange={(e) =>
                            setEditDraft({
                              ...editDraft,
                              category: e.target.value as Category,
                            })
                          }
                          className="rounded-md border border-neutral-300 bg-white px-1 py-0.5 text-xs dark:border-neutral-700 dark:bg-neutral-900"
                        >
                          {(
                            [
                              "happy_path",
                              "edge_case",
                              "negative",
                              "boundary",
                              "security",
                              "performance",
                              "accessibility",
                            ] as Category[]
                          ).map((c) => (
                            <option key={c} value={c}>
                              {c.replace("_", " ")}
                            </option>
                          ))}
                        </select>
                        <select
                          value={editDraft.priority}
                          onChange={(e) =>
                            setEditDraft({
                              ...editDraft,
                              priority: e.target.value as Priority,
                            })
                          }
                          className="rounded-md border border-neutral-300 bg-white px-1 py-0.5 text-xs dark:border-neutral-700 dark:bg-neutral-900"
                        >
                          <option value="high">high</option>
                          <option value="medium">medium</option>
                          <option value="low">low</option>
                        </select>
                      </div>
                    </div>

                    <div className="mt-3">
                      <div className="text-xs font-semibold uppercase text-neutral-500">
                        Preconditions (one per line)
                      </div>
                      <textarea
                        value={editDraft.preconditions.join("\n")}
                        onChange={(e) =>
                          setEditDraft({
                            ...editDraft,
                            preconditions: e.target.value.split("\n"),
                          })
                        }
                        rows={Math.max(2, editDraft.preconditions.length)}
                        className="mt-1 w-full rounded-md border border-neutral-300 bg-white p-2 text-sm focus:border-neutral-900 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:focus:border-neutral-200"
                      />
                    </div>

                    <div className="mt-3">
                      <div className="text-xs font-semibold uppercase text-neutral-500">
                        Steps (one per line)
                      </div>
                      <textarea
                        value={editDraft.steps.join("\n")}
                        onChange={(e) =>
                          setEditDraft({ ...editDraft, steps: e.target.value.split("\n") })
                        }
                        rows={Math.max(3, editDraft.steps.length)}
                        className="mt-1 w-full rounded-md border border-neutral-300 bg-white p-2 text-sm focus:border-neutral-900 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:focus:border-neutral-200"
                      />
                    </div>

                    <div className="mt-3">
                      <div className="text-xs font-semibold uppercase text-neutral-500">
                        Expected result
                      </div>
                      <textarea
                        value={editDraft.expected_result}
                        onChange={(e) =>
                          setEditDraft({ ...editDraft, expected_result: e.target.value })
                        }
                        rows={3}
                        className="mt-1 w-full rounded-md border border-neutral-300 bg-white p-2 text-sm focus:border-neutral-900 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:focus:border-neutral-200"
                      />
                    </div>

                    <div className="mt-4 flex items-center gap-2 border-t border-neutral-100 pt-3 dark:border-neutral-800">
                      <button
                        onClick={saveEdit}
                        className="rounded-md bg-neutral-900 px-3 py-1 text-xs font-medium text-white dark:bg-neutral-100 dark:text-neutral-900"
                      >
                        Save
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="rounded-md border border-neutral-300 px-3 py-1 text-xs hover:bg-neutral-100 dark:border-neutral-700 dark:hover:bg-neutral-800"
                      >
                        Cancel
                      </button>
                      <span className="text-xs text-neutral-500">
                        Local edit — no API call, no quota used.
                      </span>
                    </div>
                  </li>
                ) : (
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
                        <span
                          className={`rounded px-2 py-0.5 text-xs ${CATEGORY_COLORS[tc.category]}`}
                        >
                          {tc.category.replace("_", " ")}
                        </span>
                        <span
                          className={`rounded px-2 py-0.5 text-xs ${PRIORITY_COLORS[tc.priority]}`}
                        >
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

                    <div className="mt-4 border-t border-neutral-100 pt-3 dark:border-neutral-800">
                      {feedbackDraftId === tc.id ? (
                        <div className="space-y-2">
                          <textarea
                            value={feedbackDraft}
                            onChange={(e) => setFeedbackDraft(e.target.value)}
                            rows={2}
                            placeholder="What's wrong with this test case? e.g. 'expected result should include the exact error text', 'steps skip the email verification step'"
                            className="w-full rounded-md border border-neutral-300 bg-white p-2 text-xs focus:border-neutral-900 focus:outline-none dark:border-neutral-700 dark:bg-neutral-900 dark:focus:border-neutral-200"
                            autoFocus
                          />
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => handleRegenerate(tc, feedbackDraft.trim())}
                              disabled={regeneratingId === tc.id}
                              className="rounded-md bg-indigo-600 px-3 py-1 text-xs font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
                            >
                              {regeneratingId === tc.id ? "Regenerating…" : "Regenerate"}
                            </button>
                            <button
                              onClick={() => {
                                setFeedbackDraftId(null);
                                setFeedbackDraft("");
                              }}
                              disabled={regeneratingId === tc.id}
                              className="rounded-md border border-neutral-300 px-3 py-1 text-xs hover:bg-neutral-100 disabled:opacity-50 dark:border-neutral-700 dark:hover:bg-neutral-800"
                            >
                              Cancel
                            </button>
                            <span className="text-xs text-neutral-500">
                              Leave blank for a generic improvement pass.
                            </span>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center gap-3">
                          <button
                            onClick={() => {
                              setFeedbackDraftId(tc.id);
                              setFeedbackDraft("");
                            }}
                            disabled={regeneratingId !== null || editingId !== null}
                            className="text-xs text-indigo-600 hover:text-indigo-500 disabled:opacity-50 dark:text-indigo-400"
                          >
                            ↻ Regenerate with feedback
                          </button>
                          <button
                            onClick={() => startEdit(tc)}
                            disabled={regeneratingId !== null || editingId !== null}
                            className="text-xs text-neutral-600 hover:text-neutral-900 disabled:opacity-50 dark:text-neutral-400 dark:hover:text-neutral-100"
                          >
                            ✎ Edit manually
                          </button>
                        </div>
                      )}
                    </div>
                  </li>
                ),
              )}
            </ul>
          </div>
        </section>
      )}

      {usage && !usage.subscribed && usage.stripeConfigured && (
        <section id="pricing" className="mt-16">
          <h2 className="text-center text-2xl font-semibold tracking-tight">Pricing</h2>
          <p className="mt-2 text-center text-sm text-neutral-600 dark:text-neutral-400">
            Free to try. Upgrade when 3 generations a day stops cutting it.
          </p>
          <div className="mx-auto mt-8 grid max-w-3xl gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
              <div className="text-sm font-medium text-neutral-500">Free</div>
              <div className="mt-1 text-3xl font-semibold">$0</div>
              <div className="text-xs text-neutral-500">no card required</div>
              <ul className="mt-4 space-y-2 text-sm">
                <li>· 3 generations per UTC day</li>
                <li>· Text, screenshots, and URL capture</li>
                <li>· All export formats (CSV, JSON, Jira, Xray, TestRail)</li>
                <li>· Claude Opus 4.7 with adaptive thinking</li>
              </ul>
            </div>
            <div className="rounded-xl border-2 border-indigo-500 bg-white p-6 dark:bg-neutral-900">
              <div className="text-sm font-medium text-indigo-600 dark:text-indigo-400">Pro</div>
              <div className="mt-1 text-3xl font-semibold">
                $9<span className="text-base font-normal text-neutral-500">/mo</span>
              </div>
              <div className="text-xs text-neutral-500">cancel anytime</div>
              <ul className="mt-4 space-y-2 text-sm">
                <li>· <strong>Unlimited</strong> generations</li>
                <li>· Everything in Free</li>
                <li>· Priority model access</li>
                <li>· Support the roadmap (mobile crawl, direct Jira/Xray push)</li>
              </ul>
              <button
                onClick={handleUpgrade}
                disabled={upgrading}
                className="mt-6 w-full rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {upgrading ? "Redirecting…" : "Upgrade to Pro"}
              </button>
            </div>
          </div>
          <p className="mx-auto mt-6 max-w-2xl text-center text-xs text-neutral-500">
            Enterprise (teams, SSO, self-hosted)? Email us and we&apos;ll sort you out.
          </p>
        </section>
      )}

      <footer className="mt-20 border-t border-neutral-200 pt-6 text-center text-xs text-neutral-500 dark:border-neutral-800">
        Made with Claude Opus 4.7 · Test cases are suggestions; always review before
        merging to your suite.
      </footer>
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
