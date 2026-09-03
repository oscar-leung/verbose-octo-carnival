import { describe, expect, it } from 'vitest';
import type { SkitScript } from '../../../shared/types';
import { buildGrammarIndex, filterGrammarIndex, plainLineText } from './grammarIndex';
import { DEMO_SCENES, PUBLIC_SCENES } from '../data/demoScenes';

const SCENE_A: SkitScript = {
  title: 'シーンA',
  characters: [{ id: 'a', name: 'あ', color: '#fff' }],
  lines: [
    {
      id: 'a-1',
      character: 'a',
      start: 0,
      end: 2,
      tokens: [{ t: 'ヒンメル' }, { t: 'なら' }],
      grammar: [{ p: '〜なら', en: 'conditional "if it\'s ~"' }],
    },
    {
      id: 'a-2',
      character: 'a',
      start: 3,
      end: 5,
      tokens: [{ t: '老', r: 'ふ' }, { t: 'けたなあ' }],
      grammar: [
        { p: '〜なあ', en: 'emotive ending' },
        { p: '〜なら', en: 'a second explanation that must NOT win' },
      ],
    },
  ],
};

const SCENE_B: SkitScript = {
  title: 'シーンB',
  characters: [{ id: 'b', name: 'い', color: '#fff' }],
  lines: [
    {
      id: 'b-1',
      character: 'b',
      start: 0,
      end: 2,
      tokens: [{ t: '君ならできる' }],
      grammar: [{ p: '〜なら', en: 'conditional' }],
    },
    // No grammar at all — must simply be skipped.
    { id: 'b-2', character: 'b', start: 3, end: 5, tokens: [{ t: 'うん' }] },
  ],
};

describe('plainLineText', () => {
  it('joins token surfaces, ignoring readings', () => {
    expect(plainLineText([{ t: '老', r: 'ふ' }, { t: 'けたなあ' }])).toBe('老けたなあ');
  });
});

describe('buildGrammarIndex (fixture)', () => {
  const index = buildGrammarIndex([{ slug: 'scene-a', script: SCENE_A }, SCENE_B]);

  it('dedupes patterns across lines and scripts, keeping the first explanation', () => {
    expect(index.map((e) => e.pattern)).toEqual(['〜なあ', '〜なら']);
    const nara = index.find((e) => e.pattern === '〜なら')!;
    expect(nara.explanation).toBe('conditional "if it\'s ~"');
  });

  it('collects one occurrence per (script, line), with slug only when public', () => {
    const nara = index.find((e) => e.pattern === '〜なら')!;
    expect(nara.occurrences).toEqual([
      { scriptTitle: 'シーンA', slug: 'scene-a', lineId: 'a-1', lineText: 'ヒンメルなら' },
      { scriptTitle: 'シーンA', slug: 'scene-a', lineId: 'a-2', lineText: '老けたなあ' },
      { scriptTitle: 'シーンB', lineId: 'b-1', lineText: '君ならできる' },
    ]);
  });

  it('sorts Japanese-first, ignoring the leading 〜', () => {
    // なあ < なら in kana order once the tilde is stripped.
    expect(index[0]?.pattern).toBe('〜なあ');
  });

  it('is idempotent for repeated identical lines (no duplicate occurrences)', () => {
    const twice = buildGrammarIndex([SCENE_A, SCENE_A]);
    const nara = twice.find((e) => e.pattern === '〜なら')!;
    expect(nara.occurrences).toHaveLength(2); // a-1 + a-2, not 4
  });
});

describe('filterGrammarIndex', () => {
  const index = buildGrammarIndex([SCENE_A, SCENE_B]);

  it('matches pattern, explanation, and line text; empty query returns all', () => {
    expect(filterGrammarIndex(index, '')).toHaveLength(2);
    expect(filterGrammarIndex(index, '〜なら')).toHaveLength(1);
    expect(filterGrammarIndex(index, 'EMOTIVE')).toHaveLength(1);
    expect(filterGrammarIndex(index, '君なら')).toHaveLength(1);
    expect(filterGrammarIndex(index, 'zzz-nothing')).toHaveLength(0);
  });
});

describe('buildGrammarIndex (real bundled scenes)', () => {
  it('indexes the DEMO_SCENES catalogue: >40 unique patterns, no dupes', () => {
    const index = buildGrammarIndex(DEMO_SCENES);
    expect(index.length).toBeGreaterThan(40);
    const patterns = index.map((e) => e.pattern);
    expect(new Set(patterns).size).toBe(patterns.length);
    for (const entry of index) {
      expect(entry.occurrences.length).toBeGreaterThan(0);
      expect(entry.explanation.length).toBeGreaterThan(0);
    }
  });

  it('gives every PUBLIC_SCENES occurrence a linkable slug, incl. 〜なら', () => {
    const index = buildGrammarIndex(PUBLIC_SCENES);
    expect(index.length).toBeGreaterThan(40);
    const nara = index.find((e) => e.pattern === '〜なら');
    expect(nara).toBeDefined();
    expect(nara!.occurrences.every((o) => typeof o.slug === 'string' && o.slug.length > 0)).toBe(
      true
    );
    expect(nara!.occurrences.some((o) => o.slug === 'meteor-promise')).toBe(true);
  });
});
