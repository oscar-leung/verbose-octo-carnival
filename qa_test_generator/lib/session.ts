import { cookies } from "next/headers";
import { randomUUID } from "crypto";

const COOKIE_NAME = "qa_uid";
const COOKIE_MAX_AGE = 60 * 60 * 24 * 365; // 1 year

export function getOrCreateUserId(): { id: string; created: boolean } {
  const store = cookies();
  const existing = store.get(COOKIE_NAME)?.value;
  if (existing && /^[0-9a-f-]{36}$/i.test(existing)) {
    return { id: existing, created: false };
  }
  const id = randomUUID();
  store.set(COOKIE_NAME, id, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: COOKIE_MAX_AGE,
  });
  return { id, created: true };
}

export function getUserIdFromCookie(): string | null {
  const v = cookies().get(COOKIE_NAME)?.value;
  return v && /^[0-9a-f-]{36}$/i.test(v) ? v : null;
}
