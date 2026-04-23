import { getRedis, isRedisConfigured } from "./redis";

export type QuotaStatus = {
  subscribed: boolean;
  used: number;
  limit: number;
  remaining: number;
  resetAtIso: string;
};

function freeLimit(): number {
  const raw = process.env.FREE_TIER_DAILY_LIMIT;
  const n = raw ? parseInt(raw, 10) : 3;
  return Number.isFinite(n) && n > 0 ? n : 3;
}

function utcDayKey(): string {
  const d = new Date();
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `${y}${m}${day}`;
}

function nextUtcMidnightIso(): string {
  const d = new Date();
  const next = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() + 1));
  return next.toISOString();
}

async function isSubscribed(userId: string): Promise<boolean> {
  const redis = getRedis();
  if (!redis) return false;
  const sub = await redis.get<{ status: string; current_period_end: number }>(`sub:${userId}`);
  if (!sub) return false;
  if (sub.status !== "active" && sub.status !== "trialing") return false;
  if (sub.current_period_end && sub.current_period_end * 1000 < Date.now()) return false;
  return true;
}

export async function getQuotaStatus(userId: string): Promise<QuotaStatus> {
  const limit = freeLimit();
  const resetAtIso = nextUtcMidnightIso();

  if (!isRedisConfigured()) {
    return { subscribed: false, used: 0, limit, remaining: limit, resetAtIso };
  }

  const subscribed = await isSubscribed(userId);
  if (subscribed) {
    return { subscribed: true, used: 0, limit: Infinity, remaining: Infinity, resetAtIso };
  }

  const redis = getRedis()!;
  const used = (await redis.get<number>(`quota:${userId}:${utcDayKey()}`)) ?? 0;
  const remaining = Math.max(0, limit - used);
  return { subscribed: false, used, limit, remaining, resetAtIso };
}

export async function consumeQuota(userId: string): Promise<{
  allowed: boolean;
  status: QuotaStatus;
}> {
  const limit = freeLimit();
  const resetAtIso = nextUtcMidnightIso();

  if (!isRedisConfigured()) {
    return {
      allowed: true,
      status: { subscribed: false, used: 0, limit, remaining: limit, resetAtIso },
    };
  }

  const subscribed = await isSubscribed(userId);
  if (subscribed) {
    return {
      allowed: true,
      status: {
        subscribed: true,
        used: 0,
        limit: Infinity,
        remaining: Infinity,
        resetAtIso,
      },
    };
  }

  const redis = getRedis()!;
  const key = `quota:${userId}:${utcDayKey()}`;
  const used = await redis.incr(key);
  if (used === 1) {
    // Expire at end of UTC day (with buffer).
    await redis.expire(key, 60 * 60 * 26);
  }

  if (used > limit) {
    // Roll back the increment so the counter reflects actual usage cap.
    await redis.decr(key);
    return {
      allowed: false,
      status: { subscribed: false, used: limit, limit, remaining: 0, resetAtIso },
    };
  }

  return {
    allowed: true,
    status: {
      subscribed: false,
      used,
      limit,
      remaining: Math.max(0, limit - used),
      resetAtIso,
    },
  };
}
