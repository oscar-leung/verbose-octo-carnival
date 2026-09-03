import { describe, expect, it } from 'vitest';
import {
  hasKanji,
  kataToHira,
  mergePlainTokens,
  morphemesToRubyTokens,
  splitOkurigana,
  type Morpheme,
} from './furigana';

// All tests run on mock morphemes — no kuromoji dictionary needed (offline).

describe('kataToHira', () => {
  it('converts katakana to hiragana', () => {
    expect(kataToHira('タベル')).toBe('たべる');
    expect(kataToHira('ゴジュウネン')).toBe('ごじゅうねん');
  });

  it('keeps the prolonged sound mark and non-kana as-is', () => {
    expect(kataToHira('コーヒー')).toBe('こーひー');
    expect(kataToHira('漢字ABC!')).toBe('漢字ABC!');
  });

  it('handles small kana and ヴ', () => {
    expect(kataToHira('チョット')).toBe('ちょっと');
    expect(kataToHira('ヴ')).toBe('ゔ');
  });
});

describe('hasKanji', () => {
  it('detects kanji', () => {
    expect(hasKanji('食べる')).toBe(true);
    expect(hasKanji('人々')).toBe(true);
  });

  it('rejects pure kana, latin, and punctuation', () => {
    expect(hasKanji('たべる')).toBe(false);
    expect(hasKanji('カバン')).toBe(false);
    expect(hasKanji('ABC…。')).toBe(false);
  });
});

describe('splitOkurigana', () => {
  it('strips trailing okurigana', () => {
    expect(splitOkurigana('食べる', 'たべる')).toEqual([{ t: '食', r: 'た' }, { t: 'べる' }]);
    expect(splitOkurigana('見送った', 'みおくった')).toEqual([
      { t: '見送', r: 'みおく' },
      { t: 'った' },
    ]);
  });

  it('strips leading kana (honorific お etc.)', () => {
    expect(splitOkurigana('お茶', 'おちゃ')).toEqual([{ t: 'お' }, { t: '茶', r: 'ちゃ' }]);
  });

  it('strips both ends at once', () => {
    expect(splitOkurigana('お願いします', 'おねがいします')).toEqual([
      { t: 'お' },
      { t: '願', r: 'ねが' },
      { t: 'いします' },
    ]);
  });

  it('keeps the whole reading when kana sits between kanji', () => {
    expect(splitOkurigana('言い訳', 'いいわけ')).toEqual([{ t: '言い訳', r: 'いいわけ' }]);
  });

  it('matches katakana surface kana against hiragana readings', () => {
    expect(splitOkurigana('ヶ月', 'かげつ')).toEqual([{ t: 'ヶ月', r: 'かげつ' }]);
  });

  it('returns a plain token when surface and reading are the same kana', () => {
    expect(splitOkurigana('たべる', 'たべる')).toEqual([{ t: 'たべる' }]);
  });

  it('annotates whole-kanji surfaces untouched', () => {
    expect(splitOkurigana('五十年', 'ごじゅうねん')).toEqual([{ t: '五十年', r: 'ごじゅうねん' }]);
  });
});

describe('mergePlainTokens', () => {
  it('merges adjacent no-reading tokens', () => {
    expect(mergePlainTokens([{ t: 'こん' }, { t: 'に' }, { t: 'ちは' }])).toEqual([
      { t: 'こんにちは' },
    ]);
  });

  it('leaves ruby tokens as boundaries', () => {
    expect(
      mergePlainTokens([{ t: 'お' }, { t: '茶', r: 'ちゃ' }, { t: 'を' }, { t: 'ど' }, { t: 'うぞ' }])
    ).toEqual([{ t: 'お' }, { t: '茶', r: 'ちゃ' }, { t: 'をどうぞ' }]);
  });

  it('does not mutate its input tokens', () => {
    const input = [{ t: 'あ' }, { t: 'い' }];
    mergePlainTokens(input);
    expect(input).toEqual([{ t: 'あ' }, { t: 'い' }]);
  });
});

describe('morphemesToRubyTokens', () => {
  const m = (surface_form: string, reading?: string): Morpheme =>
    reading === undefined ? { surface_form } : { surface_form, reading };

  it('converts a full sentence with okurigana and kana particles', () => {
    // ご飯を食べた。 as kuromoji would emit it (katakana readings).
    const tokens = morphemesToRubyTokens([
      m('ご飯', 'ゴハン'),
      m('を', 'ヲ'),
      m('食べ', 'タベ'),
      m('た', 'タ'),
      m('。', '。'),
    ]);
    expect(tokens).toEqual([
      { t: 'ご', },
      { t: '飯', r: 'はん' },
      { t: 'を' },
      { t: '食', r: 'た' },
      { t: 'べた。' },
    ]);
  });

  it('leaves kana-only and unknown tokens plain, merged together', () => {
    const tokens = morphemesToRubyTokens([m('カバン', 'カバン'), m('だ', 'ダ'), m('ヨォ')]);
    expect(tokens).toEqual([{ t: 'カバンだヨォ' }]);
  });

  it('treats a "*" reading as no reading', () => {
    expect(morphemesToRubyTokens([m('謎肉', '*')])).toEqual([{ t: '謎肉' }]);
  });

  it('skips empty surfaces and handles an empty analysis', () => {
    expect(morphemesToRubyTokens([])).toEqual([]);
    expect(morphemesToRubyTokens([m('', 'ア')])).toEqual([]);
  });

  it('produces round-trippable tokens for a demo-style line', () => {
    const tokens = morphemesToRubyTokens([
      m('五十年', 'ゴジュウネン'),
      m('ぶり', 'ブリ'),
      m('だ', 'ダ'),
      m('ね', 'ネ'),
      m('。', '。'),
    ]);
    expect(tokens).toEqual([{ t: '五十年', r: 'ごじゅうねん' }, { t: 'ぶりだね。' }]);
  });
});
