import { NextRequest, NextResponse } from "next/server";
import {
  captureUrlScreenshot,
  isScreenshotConfigured,
  type ScreenshotViewport,
} from "@/lib/screenshot";

export const runtime = "nodejs";
export const maxDuration = 60;

export async function POST(req: NextRequest) {
  if (!isScreenshotConfigured()) {
    return NextResponse.json(
      {
        error:
          "URL screenshots are not configured. Add SCREENSHOTONE_ACCESS_KEY from screenshotone.com.",
      },
      { status: 501 },
    );
  }

  let body: { url?: unknown; viewport?: unknown };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body." }, { status: 400 });
  }

  const rawUrl = typeof body.url === "string" ? body.url.trim() : "";
  if (!rawUrl) {
    return NextResponse.json({ error: "Missing url." }, { status: 400 });
  }

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

  try {
    const { mediaType, base64 } = await captureUrlScreenshot(parsed.toString(), viewport);
    const bytes = Math.floor((base64.length * 3) / 4);
    return NextResponse.json({ mediaType, base64, bytes, viewport });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Screenshot capture failed.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
