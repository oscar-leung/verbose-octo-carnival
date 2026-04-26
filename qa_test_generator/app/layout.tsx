import type { Metadata } from "next";
import "./globals.css";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "https://qa-test-generator.example";
const TITLE = "QA Test Case Generator — Paste a feature, get 15+ structured tests";
const DESCRIPTION =
  "AI-generated QA test cases for SDETs. Paste a spec, drop screenshots, or crawl a URL. Exports to Jira, Xray, TestRail, CSV, or pushes directly via API.";

export const metadata: Metadata = {
  metadataBase: new URL(APP_URL),
  title: TITLE,
  description: DESCRIPTION,
  applicationName: "QA Test Case Generator",
  keywords: [
    "QA",
    "SDET",
    "test cases",
    "test case generator",
    "Jira",
    "Xray",
    "TestRail",
    "Claude",
    "AI testing",
  ],
  openGraph: {
    type: "website",
    url: APP_URL,
    title: TITLE,
    description: DESCRIPTION,
    siteName: "QA Test Case Generator",
  },
  twitter: {
    card: "summary_large_image",
    title: TITLE,
    description: DESCRIPTION,
  },
  icons: {
    icon: [{ url: "/icon.svg", type: "image/svg+xml" }],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-neutral-50 text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
        {children}
      </body>
    </html>
  );
}
