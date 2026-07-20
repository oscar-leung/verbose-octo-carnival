import { describe, expect, it } from 'vitest';
import { kataToHira, levenshtein, normalizeJa, scoreAttempt, similarity } from './speech';
import type { ScriptLine } from '../../../shared/types';

const line: ScriptLine = {
  id: 'l1',
  character: 'heiter',
  start: 5,
  end: 9,
  tokens: [
    { t: '王都', r: 'おうと' },
    { t: 'は' },
    { t: '今日', r: 'きょう' },
    { t: 'もにぎやかですね。' },
  ],
};

describe('kataToHira', () => {
  it('converts katakana and leaves everything else', () => {
    expect(kataToHira('オウト')).toBe('おうと');
    expect(kataToHira('王都ですネ')).toBe('王都ですね');
  });
});

describe('normalizeJa', () => {
  it('strips punctuation and spaces, folds katakana', () => {
    expect(normalizeJa('王都は、 今日も！ニギヤカ ですね。')).toBe('王都は今日もにぎやかですね');
  });
});

describe('levenshtein / similarity', () => {
  it('computes edit distance', () => {
    expect(levenshtein('こんにちは', 'こんばんは')).toBe(2);
    expect(similarity('あああ', 'あああ')).toBe(1);
    expect(similarity('', '')).toBe(1);
  });
});

describe('scoreAttempt', () => {
  it('gives 100 for an exact surface match', () => {
    expect(scoreAttempt('王都は今日もにぎやかですね。', line)).toBe(100);
  });
  it('accepts the all-kana reading form', () => {
    expect(scoreAttempt('おうとはきょうもにぎやかですね', line)).toBe(100);
  });
  it('accepts katakana output from the recognizer', () => {
    expect(scoreAttempt('オウトハキョウモニギヤカデスネ', line)).toBeGreaterThanOrEqual(95);
  });
  it('scores partial attempts lower', () => {
    const s = scoreAttempt('今日もにぎやか', line);
    expect(s).toBeGreaterThan(30);
    expect(s).toBeLessThan(70);
  });
  it('gives 0 for empty/noise input', () => {
    expect(scoreAttempt('', line)).toBe(0);
    expect(scoreAttempt('。、！', line)).toBe(0);
  });
});
