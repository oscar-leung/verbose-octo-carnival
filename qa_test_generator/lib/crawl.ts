import * as cheerio from "cheerio";
import { captureUrlScreenshot, type ScreenshotViewport } from "./screenshot";

export type CrawlResult = {
  captures: Array<{
    url: string;
    mediaType: "image/png";
    base64: string;
  }>;
  skipped: Array<{ url: string; reason: string }>;
};

const EXTENSIONS_TO_SKIP = [
  ".pdf", ".zip", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
  ".mp4", ".mp3", ".mov", ".avi", ".ico", ".css", ".js", ".json",
  ".xml", ".rss", ".atom", ".woff", ".woff2", ".ttf", ".eot",
];

function looksLikeHtmlUrl(url: URL): boolean {
  const pathLower = url.pathname.toLowerCase();
  return !EXTENSIONS_TO_SKIP.some((ext) => pathLower.endsWith(ext));
}

async function discoverSameOriginLinks(startUrl: string, maxLinks: number): Promise<string[]> {
  const start = new URL(startUrl);
  const res = await fetch(startUrl, {
    headers: {
      "User-Agent":
        "Mozilla/5.0 (compatible; QATestGenerator/1.0; +https://example.com/bot)",
      Accept: "text/html,application/xhtml+xml",
    },
    redirect: "follow",
  });
  if (!res.ok) {
    throw new Error(`Could not fetch ${startUrl}: HTTP ${res.status}`);
  }
  const contentType = res.headers.get("content-type") ?? "";
  if (!contentType.includes("html")) {
    throw new Error(`URL returned ${contentType}, not HTML.`);
  }
  const html = await res.text();
  const $ = cheerio.load(html);
  const seen = new Set<string>([start.toString()]);
  const out: string[] = [];

  $("a[href]").each((_, el) => {
    const href = $(el).attr("href");
    if (!href) return;
    let abs: URL;
    try {
      abs = new URL(href, start);
    } catch {
      return;
    }
    // Strip hash fragments so /docs#intro and /docs#api don't count as separate pages.
    abs.hash = "";
    if (abs.hostname !== start.hostname) return;
    if (abs.protocol !== "http:" && abs.protocol !== "https:") return;
    if (!looksLikeHtmlUrl(abs)) return;
    const s = abs.toString();
    if (seen.has(s)) return;
    seen.add(s);
    out.push(s);
  });

  return out.slice(0, maxLinks);
}

/**
 * Crawl same-origin pages starting from `startUrl`, returning one screenshot per
 * discovered page (plus the start page itself). Up to `maxPages` pages total,
 * bounded by the caller and by the remaining screenshot quota on the client.
 */
export async function crawlAndCapture(
  startUrl: string,
  viewport: ScreenshotViewport,
  maxPages: number,
): Promise<CrawlResult> {
  if (maxPages < 1) throw new Error("maxPages must be >= 1");

  const captures: CrawlResult["captures"] = [];
  const skipped: CrawlResult["skipped"] = [];

  // Always screenshot the start URL first.
  try {
    const shot = await captureUrlScreenshot(startUrl, viewport);
    captures.push({ url: startUrl, ...shot });
  } catch (err) {
    const reason = err instanceof Error ? err.message : "capture failed";
    skipped.push({ url: startUrl, reason });
    // If the start URL fails, skip link discovery too — same-origin requirement
    // can't be satisfied.
    return { captures, skipped };
  }

  if (maxPages === 1) return { captures, skipped };

  // Discover additional same-origin links and screenshot them.
  let extraLinks: string[] = [];
  try {
    extraLinks = await discoverSameOriginLinks(startUrl, maxPages - 1);
  } catch (err) {
    const reason = err instanceof Error ? err.message : "link discovery failed";
    skipped.push({ url: startUrl, reason: `link discovery: ${reason}` });
  }

  for (const url of extraLinks) {
    if (captures.length >= maxPages) break;
    try {
      const shot = await captureUrlScreenshot(url, viewport);
      captures.push({ url, ...shot });
    } catch (err) {
      const reason = err instanceof Error ? err.message : "capture failed";
      skipped.push({ url, reason });
    }
  }

  return { captures, skipped };
}
