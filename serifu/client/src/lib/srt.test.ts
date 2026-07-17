import { describe, expect, it } from 'vitest';
import { joinCueLines, parseCues, parseRubyText, parseTimestamp, rubyTokensToText } from './srt';

const NL = String.fromCharCode(10);

describe('parseTimestamp', () => {
  it('parses SRT style hh:mm:ss,mmm', () => {
    expect(parseTimestamp('00:01:02,500')).toBeCloseTo(62.5);
  });
  it('parses VTT style with dot and no hours', () => {
    expect(parseTimestamp('01:02.500')).toBeCloseTo(62.5);
    expect(parseTimestamp('1:02:03.250')).toBeCloseTo(3723.25);
  });
  it('rejects garbage', () => {
    expect(parseTimestamp('abc')).toBeNull();
  });
});

describe('parseRubyText', () => {
  it('attaches readings to trailing kanji runs', () => {
    expect(parseRubyText('王都《おうと》はにぎやか')).toEqual([
      { t: '王都', r: 'おうと' },
      { t: 'はにぎやか' },
    ]);
  });
  it('supports explicit ｜ base markers', () => {
    expect(parseRubyText('あの｜流星群《りゅうせいぐん》を見た')).toEqual([
      { t: 'あの' },
      { t: '流星群', r: 'りゅうせいぐん' },
      { t: 'を見た' },
    ]);
  });
  it('passes through plain text as one token', () => {
    expect(parseRubyText('まあね。')).toEqual([{ t: 'まあね。' }]);
  });
  it('handles multiple ruby groups in one line', () => {
    expect(parseRubyText('勇者《ゆうしゃ》と魔法使《まほうつか》い')).toEqual([
      { t: '勇者', r: 'ゆうしゃ' },
      { t: 'と' },
      { t: '魔法使', r: 'まほうつか' },
      { t: 'い' },
    ]);
  });
  it('round-trips through rubyTokensToText', () => {
    const text = 'あの｜流星群《りゅうせいぐん》を見た';
    const tokens = parseRubyText(text);
    expect(parseRubyText(rubyTokensToText(tokens))).toEqual(tokens);
  });
});

describe('joinCueLines', () => {
  it('adds spaces between latin lines but not japanese', () => {
    expect(joinCueLines(['Hello there,', 'General Kenobi'])).toBe('Hello there, General Kenobi');
    expect(joinCueLines(['十年間の冒険も、', 'これで終わりだ'])).toBe('十年間の冒険も、これで終わりだ');
  });
});

describe('parseCues', () => {
  it('parses a basic SRT file', () => {
    const srt = [
      '1',
      '00:00:05,000 --> 00:00:08,200',
      '王都は今日もにぎやかですね。',
      '',
      '2',
      '00:00:09,500 --> 00:00:14,000',
      '十年間の冒険も、',
      'これで終わりだな。',
      '',
    ].join(NL);
    const cues = parseCues(srt);
    expect(cues).toHaveLength(2);
    expect(cues[0]?.start).toBeCloseTo(5);
    expect(cues[0]?.text).toBe('王都は今日もにぎやかですね。');
    expect(cues[1]?.text).toBe('十年間の冒険も、これで終わりだな。');
  });

  it('parses WebVTT with header and cue settings', () => {
    const vtt = [
      'WEBVTT',
      '',
      'NOTE this is a comment',
      '',
      '00:05.000 --> 00:08.200 align:middle',
      '<i>まあね。</i>',
      '',
    ].join(NL);
    const cues = parseCues(vtt);
    expect(cues).toHaveLength(1);
    expect(cues[0]?.text).toBe('まあね。');
    expect(cues[0]?.end).toBeCloseTo(8.2);
  });

  it('tolerates missing index numbers and CRLF', () => {
    const CR = String.fromCharCode(13);
    const srt = `00:00:01,000 --> 00:00:02,000${CR}${NL}こんにちは${CR}${NL}${CR}${NL}`;
    const cues = parseCues(srt);
    expect(cues).toHaveLength(1);
    expect(cues[0]?.text).toBe('こんにちは');
  });

  it('returns an empty list for non-subtitle text', () => {
    expect(parseCues('just some prose with no timestamps')).toEqual([]);
  });
});
