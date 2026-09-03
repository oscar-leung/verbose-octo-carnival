import { describe, expect, it } from 'vitest';
import { createBucket, tryTake } from './rateLimit';

describe('token bucket', () => {
  it('allows a full burst up to capacity, then rejects', () => {
    const b = createBucket(40, 10_000, 0);
    for (let i = 0; i < 40; i++) {
      expect(tryTake(b, 0)).toBe(true);
    }
    expect(tryTake(b, 0)).toBe(false);
    expect(tryTake(b, 1)).toBe(false); // 1ms refills only 0.004 tokens
  });

  it('refills continuously at capacity/window', () => {
    const b = createBucket(40, 10_000, 0);
    for (let i = 0; i < 40; i++) tryTake(b, 0);
    expect(tryTake(b, 0)).toBe(false);
    // 250ms at 4 tokens/s = exactly 1 token.
    expect(tryTake(b, 250)).toBe(true);
    expect(tryTake(b, 250)).toBe(false);
    // 500ms more = 2 tokens.
    expect(tryTake(b, 750)).toBe(true);
    expect(tryTake(b, 750)).toBe(true);
    expect(tryTake(b, 750)).toBe(false);
  });

  it('never refills beyond capacity', () => {
    const b = createBucket(5, 1_000, 0);
    // A long idle stretch must not bank more than `capacity` events.
    for (let i = 0; i < 5; i++) expect(tryTake(b, 60_000)).toBe(true);
    expect(tryTake(b, 60_000)).toBe(false);
  });

  it('treats a backwards clock jump as zero elapsed time', () => {
    const b = createBucket(2, 1_000, 5_000);
    expect(tryTake(b, 5_000)).toBe(true);
    expect(tryTake(b, 5_000)).toBe(true);
    expect(tryTake(b, 1_000)).toBe(false); // clock went backwards: no refill
    expect(tryTake(b, 5_500)).toBe(true); // forward again: refill resumes
  });

  it('stays untouched by normal usage rates (40 per 10s is generous)', () => {
    const b = createBucket(40, 10_000, 0);
    // Simulate a busy but human session: 3 events per second for a minute.
    let now = 0;
    for (let i = 0; i < 180; i++) {
      now += 333;
      expect(tryTake(b, now)).toBe(true);
    }
  });

  it('rejects nonsensical bucket parameters', () => {
    expect(() => createBucket(0, 1_000, 0)).toThrow();
    expect(() => createBucket(-1, 1_000, 0)).toThrow();
    expect(() => createBucket(Number.NaN, 1_000, 0)).toThrow();
    expect(() => createBucket(40, 0, 0)).toThrow();
    expect(() => createBucket(40, Number.POSITIVE_INFINITY, 0)).toThrow();
  });
});
