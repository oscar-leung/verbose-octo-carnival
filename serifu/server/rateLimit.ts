// Pure token-bucket rate limiter. No timers, no globals — callers pass the
// clock in, which keeps the math unit-testable and the server wiring trivial.

export interface TokenBucket {
  /** Maximum tokens the bucket can hold (also the burst size). */
  readonly capacity: number;
  /** Tokens regained per millisecond. */
  readonly refillPerMs: number;
  /** Tokens currently available (fractional between refills). */
  tokens: number;
  /** ms timestamp of the last refill computation. */
  lastRefillAt: number;
}

/**
 * A bucket that allows `capacity` events per `windowMs` sliding-ish window:
 * it starts full (burst of `capacity`) and refills continuously at
 * `capacity / windowMs` tokens per ms.
 */
export function createBucket(capacity: number, windowMs: number, now: number): TokenBucket {
  if (!Number.isFinite(capacity) || capacity <= 0) {
    throw new Error('capacity must be a positive finite number');
  }
  if (!Number.isFinite(windowMs) || windowMs <= 0) {
    throw new Error('windowMs must be a positive finite number');
  }
  return {
    capacity,
    refillPerMs: capacity / windowMs,
    tokens: capacity,
    lastRefillAt: now,
  };
}

/**
 * Try to consume one token at time `now`. Returns true if the event should
 * be allowed, false if it should be dropped. Mutates the bucket.
 */
export function tryTake(bucket: TokenBucket, now: number): boolean {
  // Refill for elapsed time; a backwards clock jump refills nothing.
  const elapsed = Math.max(0, now - bucket.lastRefillAt);
  bucket.tokens = Math.min(bucket.capacity, bucket.tokens + elapsed * bucket.refillPerMs);
  bucket.lastRefillAt = Math.max(bucket.lastRefillAt, now);
  if (bucket.tokens < 1) return false;
  bucket.tokens -= 1;
  return true;
}
