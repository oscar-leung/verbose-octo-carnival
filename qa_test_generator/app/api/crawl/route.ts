import { NextRequest, NextResponse } from "next/server";
import { crawlAndCapture } from "@/lib/crawl";
import { isScreenshotConfigured, type ScreenshotViewport } from "@/lib/screenshot";

export const runtime = "nodejs";
export const maxDuration = 120;

const MAX_PAGES_HARD_CAP = 5;

export async function POST(req: NextRequest) {
  if (!isScreenshotConfigured()) {
    return NextResponse.json(
      {
        error:
          "URL capture is not configured. Add SCREENSHOTONE_ACCESS_KEY from screenshotone.com.",
      },
      { status: 501 },
    );
  }

  let body: { url?: unknown; viewport?: unknown; maxPages?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const rawUrl = typeof body.url === "string" ? body.url.trim() : "";
  if (!rawUrl) return NextResponse.json({ error: "Missing url." }, { status: 400 });

  let parsed: URL;
  try {
    parsed = new URL(rawUrl);
  } catch {
    return NextResponse.json({ error: "URL is not valid." }, { status: 400 });
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    return NextResponse.json(
      { error: "URL must start with http:// or https://." },
      { status: 400 },
    );
  }

  const viewport: ScreenshotViewport = body.viewport === "mobile" ? "mobile" : "desktop";

  const rawMaxPages = typeof body.maxPages === "number" ? Math.floor(body.maxPages) : 3;
  const maxPages = Math.min(Math.max(rawMaxPages, 1), MAX_PAGES_HARD_CAP);

  try {
    const result = await crawlAndCapture(parsed.toString(), viewport, maxPages);
    return NextResponse.json(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Crawl failed.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
