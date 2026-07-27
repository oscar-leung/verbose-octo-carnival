import { describe, expect, it } from 'vitest';
import { maskTokens } from '../components/SoloPractice';

const tokens = [
  { t: '王都', r: 'おうと' },
  { t: 'は' },
  { t: '今日', r: 'きょう' },
  { t: 'もにぎやかですね。' },
];

describe('maskTokens', () => {
  it('level 0 leaves tokens untouched', () => {
    expect(maskTokens(tokens, 0)).toEqual(tokens);
  });
  it('level 1 drops readings but keeps text', () => {
    const masked = maskTokens(tokens, 1);
    expect(masked[0]).toEqual({ t: '王都' });
    expect(masked.every((t) => !('r' in t))).toBe(true);
  });
  it('level 2 keeps only the first character of each token', () => {
    const masked = maskTokens(tokens, 2);
    expect(masked[0]?.t).toBe('王＿');
    expect(masked[3]?.t).toBe('も＿＿＿＿＿＿＿＿');
  });
  it('level 3 hides everything', () => {
    const masked = maskTokens(tokens, 3);
    expect(masked[0]?.t).toBe('＿＿');
    expect(masked[1]?.t).toBe('＿');
  });
});
