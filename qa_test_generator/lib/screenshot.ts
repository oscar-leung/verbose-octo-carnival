export type ScreenshotViewport = "desktop" | "mobile";

export type CapturedScreenshot = {
  mediaType: "image/png";
  base64: string;
};

export function isScreenshotConfigured(): boolean {
  return Boolean(process.env.SCREENSHOTONE_ACCESS_KEY);
}

/**
 * Capture a full-page screenshot of a public URL via ScreenshotOne.
 * Sign up at https://screenshotone.com/ (100 free screenshots/month).
 * Set SCREENSHOTONE_ACCESS_KEY in your environment.
 */
export async function captureUrlScreenshot(
  url: string,
  viewport: ScreenshotViewport = "desktop",
): Promise<CapturedScreenshot> {
  const accessKey = process.env.SCREENSHOTONE_ACCESS_KEY;
  if (!accessKey) {
    throw new Error(
      "URL screenshots require SCREENSHOTONE_ACCESS_KEY. Sign up at screenshotone.com (100 free screenshots/month).",
    );
  }

  const params = new URLSearchParams({
    access_key: accessKey,
    url,
    format: "png",
    block_ads: "true",
    block_cookie_banners: "true",
    block_trackers: "true",
    cache: "true",
    cache_ttl: "3600",
    wait_until: "networkidle0",
    full_page: "true",
    timeout: "45",
  });

  if (viewport === "desktop") {
    params.set("viewport_width", "1440");
    params.set("viewport_height", "900");
    params.set("device_scale_factor", "1");
  } else {
    params.set("viewport_width", "390");
    params.set("viewport_height", "844");
    params.set("device_scale_factor", "2");
  }

  const apiUrl = `https://api.screenshotone.com/take?${params.toString()}`;
  const res = await fetch(apiUrl, { cache: "no-store" });
  if (!res.ok) {
    let detail = "";
    try {
      detail = (await res.text()).slice(0, 300);
    } catch {
      // ignore
    }
    throw new Error(`Screenshot service returned ${res.status}: ${detail || "no body"}`);
  }

  const buf = await res.arrayBuffer();
  const base64 = Buffer.from(buf).toString("base64");
  return { mediaType: "image/png", base64 };
}
