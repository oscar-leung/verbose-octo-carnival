import { describe, expect, it } from 'vitest';
import {
  applyReview,
  bandCounts,
  bandFor,
  dueEntries,
  INTERVALS_MS,
  MAX_LEVEL,
  mergeExposure,
  type MasteryEntry,
} from './mastery';

const NOW = 1_000_000;

function entry(overrides: Partial<MasteryEntry>): MasteryEntry {
  return {
    key: 'vocab:王都',
    kind: 'vocab',
    front: '王都',
    back: 'royal capital',
    level: 0,
    streak: 0,
    seen: 1,
    reviews: 0,
    correct: 0,
    due: NOW,
    addedAt: NOW,
    ...overrides,
  };
}

describe('bandFor', () => {
  it('maps levels to bands', () => {
    expect(bandFor(0)).toBe('新規');
    expect(bandFor(1)).toBe('学習中');
    expect(bandFor(2)).toBe('学習中');
    expect(bandFor(3)).toBe('定着');
    expect(bandFor(4)).toBe('定着');
    expect(bandFor(5)).toBe('マスター');
  });
});

describe('mergeExposure', () => {
  it('adds new items at level 0 due immediately', () => {
    const merged = mergeExposure([], [{ kind: 'vocab', front: '王都', reading: 'おうと', back: 'capital' }], NOW);
    expect(merged).toHaveLength(1);
    expect(merged[0]?.level).toBe(0);
    expect(merged[0]?.due).toBe(NOW);
    expect(merged[0]?.seen).toBe(1);
  });
  it('increments seen for repeats without touching level', () => {
    const first = mergeExposure([], [{ kind: 'grammar', front: '〜なら', back: 'conditional' }], NOW);
    const leveled = [{ ...first[0]!, level: 3 }];
    const again = mergeExposure(leveled, [{ kind: 'grammar', front: '〜なら', back: 'conditional' }], NOW + 5);
    expect(again).toHaveLength(1);
    expect(again[0]?.seen).toBe(2);
    expect(again[0]?.level).toBe(3);
  });
});

describe('applyReview', () => {
  it('promotes on correct with growing intervals', () => {
    let e = entry({});
    e = applyReview(e, true, NOW);
    expect(e.level).toBe(1);
    expect(e.due).toBe(NOW + INTERVALS_MS[1]!);
    e = applyReview(e, true, NOW);
    expect(e.level).toBe(2);
    expect(e.streak).toBe(2);
  });
  it('caps at max level', () => {
    const e = applyReview(entry({ level: MAX_LEVEL }), true, NOW);
    expect(e.level).toBe(MAX_LEVEL);
  });
  it('drops two levels on a miss and resets streak', () => {
    const e = applyReview(entry({ level: 4, streak: 6 }), false, NOW);
    expect(e.level).toBe(2);
    expect(e.streak).toBe(0);
    expect(e.due).toBe(NOW + INTERVALS_MS[2]!);
  });
});

describe('dueEntries / bandCounts', () => {
  it('filters and sorts due items', () => {
    const list = [entry({ key: 'a', due: NOW + 999 }), entry({ key: 'b', due: NOW - 5 }), entry({ key: 'c', due: NOW - 50 })];
    expect(dueEntries(list, NOW).map((e) => e.key)).toEqual(['c', 'b']);
  });
  it('counts bands', () => {
    const counts = bandCounts([entry({ level: 0 }), entry({ key: 'x', level: 2 }), entry({ key: 'y', level: 5 })]);
    expect(counts['新規']).toBe(1);
    expect(counts['学習中']).toBe(1);
    expect(counts['マスター']).toBe(1);
  });
});
