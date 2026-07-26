/**
 * Mastery tracker: every vocab word and grammar pattern you successfully
 * SPEAK enters this ledger, then short spaced-repetition reviews move items
 * up Leitner levels. Pure logic lives in exported functions (unit-tested);
 * localStorage is only touched by the thin load/save wrappers.
 */

export type MasteryKind = 'vocab' | 'grammar';
export type MasteryBand = '新規' | '学習中' | '定着' | 'マスター';

export interface MasteryEntry {
  key: string;
  kind: MasteryKind;
  /** The word or pattern itself. */
  front: string;
  reading?: string;
  /** English gloss/explanation. */
  back: string;
  /** Leitner level 0-5. */
  level: number;
  streak: number;
  /** Times encountered in passed spoken lines. */
  seen: number;
  reviews: number;
  correct: number;
  /** ms epoch when this item is next due for review. */
  due: number;
  addedAt: number;
}

export interface ExposureItem {
  kind: MasteryKind;
  front: string;
  reading?: string;
  back: string;
}

const DAY = 24 * 60 * 60 * 1000;
/** Review intervals per Leitner level. */
export const INTERVALS_MS = [0, 1 * DAY, 3 * DAY, 7 * DAY, 14 * DAY, 30 * DAY];
export const MAX_LEVEL = INTERVALS_MS.length - 1;

export function masteryKey(kind: MasteryKind, front: string): string {
  return `${kind}:${front}`;
}

export function bandFor(level: number): MasteryBand {
  if (level <= 0) return '新規';
  if (level <= 2) return '学習中';
  if (level <= 4) return '定着';
  return 'マスター';
}

/** Merge encountered items into the ledger (new items start at level 0, due now). */
export function mergeExposure(
  entries: MasteryEntry[],
  items: ExposureItem[],
  now: number
): MasteryEntry[] {
  const byKey = new Map(entries.map((e) => [e.key, e]));
  for (const item of items) {
    const key = masteryKey(item.kind, item.front);
    const existing = byKey.get(key);
    if (existing) {
      existing.seen += 1;
    } else {
      byKey.set(key, {
        key,
        kind: item.kind,
        front: item.front,
        ...(item.reading ? { reading: item.reading } : {}),
        back: item.back,
        level: 0,
        streak: 0,
        seen: 1,
        reviews: 0,
        correct: 0,
        due: now,
        addedAt: now,
      });
    }
  }
  return [...byKey.values()];
}

/** Grade one review: correct promotes a level, a miss drops two. */
export function applyReview(entry: MasteryEntry, correct: boolean, now: number): MasteryEntry {
  const level = correct ? Math.min(MAX_LEVEL, entry.level + 1) : Math.max(0, entry.level - 2);
  return {
    ...entry,
    level,
    streak: correct ? entry.streak + 1 : 0,
    reviews: entry.reviews + 1,
    correct: entry.correct + (correct ? 1 : 0),
    due: now + (INTERVALS_MS[level] ?? 0),
  };
}

export function dueEntries(entries: MasteryEntry[], now: number): MasteryEntry[] {
  return entries.filter((e) => e.due <= now).sort((a, b) => a.due - b.due);
}

export function bandCounts(entries: MasteryEntry[]): Record<MasteryBand, number> {
  const counts: Record<MasteryBand, number> = { 新規: 0, 学習中: 0, 定着: 0, マスター: 0 };
  for (const e of entries) counts[bandFor(e.level)] += 1;
  return counts;
}

// ---- storage ----

const KEY = 'serifu:mastery';
const MAX_ENTRIES = 5000;

export function loadMastery(): MasteryEntry[] {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return [];
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (e): e is MasteryEntry =>
        typeof e === 'object' &&
        e !== null &&
        typeof (e as MasteryEntry).key === 'string' &&
        typeof (e as MasteryEntry).front === 'string' &&
        typeof (e as MasteryEntry).level === 'number'
    );
  } catch {
    return [];
  }
}

export function saveMastery(entries: MasteryEntry[]): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(entries.slice(0, MAX_ENTRIES)));
  } catch {
    // storage unavailable — session-only
  }
}

/** Record that these items were part of a successfully spoken line. */
export function recordExposure(items: ExposureItem[]): void {
  if (items.length === 0) return;
  saveMastery(mergeExposure(loadMastery(), items, Date.now()));
}

export function gradeReview(key: string, correct: boolean): void {
  const entries = loadMastery();
  const i = entries.findIndex((e) => e.key === key);
  const entry = entries[i];
  if (!entry) return;
  entries[i] = applyReview(entry, correct, Date.now());
  saveMastery(entries);
}
