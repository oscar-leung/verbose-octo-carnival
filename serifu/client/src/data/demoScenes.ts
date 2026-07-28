import type { Character, ScriptLine, SkitScript } from '../../../shared/types';
import { DEMO_SCRIPT } from './demoScript';

/**
 * Bundled Frieren demo scenes — short, approximate recreations for practicing
 * before importing a real episode's subtitles. Timestamps are placeholders;
 * line up with your video via the editor's shift tool or your sync offset.
 */

/** Fifty years later: the reunion and Himmel's funeral (ep. 1's turning point). */
export const SCENE_FUNERAL: SkitScript = {
  title: '葬送のフリーレン — 五十年後の再会 (デモ)',
  characters: [
    { id: 'frieren', name: 'フリーレン', color: '#7ecbff' },
    { id: 'heiter', name: 'ハイター', color: '#a6e3a1' },
    { id: 'eisen', name: 'アイゼン', color: '#ffb86c' },
  ],
  lines: [
    {
      id: 'fn-1',
      character: 'frieren',
      start: 5,
      end: 9.5,
      tokens: [
        { t: '五十年', r: 'ごじゅうねん' },
        { t: 'ぶりだね。みんな、' },
        { t: '老', r: 'ふ' },
        { t: 'けたなあ。' },
      ],
      translation: "It's been fifty years. Everyone's gotten so old.",
      vocab: [
        { w: '〜ぶり', en: 'for the first time in ~ (五十年ぶり = first time in 50 years)' },
        { w: '老ける', r: 'ふける', en: 'to age, to grow old' },
      ],
      grammar: [
        { p: '期間＋ぶり', en: 'elapsed time since something last happened' },
        { p: '〜なあ', en: 'emotive sentence ending — feeling it as you say it' },
      ],
    },
    {
      id: 'fn-2',
      character: 'heiter',
      start: 10,
      end: 14.5,
      tokens: [
        { t: 'ヒンメルは、' },
        { t: '眠', r: 'ねむ' },
        { t: 'るように' },
        { t: '逝', r: 'い' },
        { t: 'きましたよ。' },
      ],
      translation: 'Himmel passed away peacefully, as if falling asleep.',
      vocab: [
        { w: '眠る', r: 'ねむる', en: 'to sleep' },
        { w: '逝く', r: 'いく', en: 'to pass away (gentle euphemism)' },
      ],
      grammar: [{ p: '〜ように', en: '"as if ~ / like ~" — comparing the manner' }],
    },
    {
      id: 'fn-3',
      character: 'eisen',
      start: 15,
      end: 18.5,
      tokens: [
        { t: '五十年', r: 'ごじゅうねん' },
        { t: 'だからな。' },
        { t: '当然', r: 'とうぜん' },
        { t: 'だ。' },
      ],
      translation: "It has been fifty years, after all. It's only natural.",
      vocab: [{ w: '当然', r: 'とうぜん', en: 'natural, to be expected' }],
      grammar: [{ p: '〜だから', en: 'gives the reason: "because it\'s been 50 years"' }],
    },
    {
      id: 'fn-4',
      character: 'frieren',
      start: 19,
      end: 23.5,
      tokens: [
        { t: '私', r: 'わたし' },
        { t: 'は、' },
        { t: '何', r: 'なに' },
        { t: 'も' },
        { t: '変', r: 'か' },
        { t: 'わっていないのにね。' },
      ],
      translation: "Even though I haven't changed at all.",
      vocab: [{ w: '変わる', r: 'かわる', en: 'to change' }],
      grammar: [
        { p: '〜のに', en: 'contrast with feeling: "even though…"' },
        { p: '何も＋negative', en: '"nothing at all" — 何も…ていない' },
      ],
    },
    {
      id: 'fn-5',
      character: 'frieren',
      start: 24,
      end: 28.5,
      tokens: [
        { t: '私', r: 'わたし' },
        { t: '、ヒンメルのことを' },
        { t: '何', r: 'なに' },
        { t: 'も' },
        { t: '知', r: 'し' },
        { t: 'らない。' },
      ],
      translation: "I… don't know anything about Himmel.",
      vocab: [{ w: '知る', r: 'しる', en: 'to know' }],
      grammar: [{ p: '人＋のこと', en: '"about (a person)" — the person as a whole' }],
    },
    {
      id: 'fn-6',
      character: 'frieren',
      start: 29,
      end: 33.5,
      tokens: [
        { t: 'たった' },
        { t: '十年', r: 'じゅうねん' },
        { t: '、' },
        { t: '一緒', r: 'いっしょ' },
        { t: 'に' },
        { t: '旅', r: 'たび' },
        { t: 'をしただけだし。' },
      ],
      translation: 'We only traveled together for ten years, after all.',
      vocab: [
        { w: '一緒に', r: 'いっしょに', en: 'together' },
        { w: '旅', r: 'たび', en: 'journey, travels' },
      ],
      grammar: [
        { p: '〜だけ', en: '"only, just ~"' },
        { p: '〜し', en: 'lists a reason, trailing off' },
      ],
    },
    {
      id: 'fn-7',
      character: 'frieren',
      start: 34,
      end: 38.5,
      tokens: [
        { t: 'なのに、どうして' },
        { t: '涙', r: 'なみだ' },
        { t: 'が' },
        { t: '止', r: 'と' },
        { t: 'まらないんだろう。' },
      ],
      translation: "And yet… why won't my tears stop?",
      vocab: [
        { w: '涙', r: 'なみだ', en: 'tears' },
        { w: '止まる', r: 'とまる', en: 'to stop (by itself)' },
      ],
      grammar: [
        { p: 'なのに', en: '"and yet / despite that" — strong contrast opener' },
        { p: '〜んだろう', en: 'wondering aloud to oneself' },
      ],
    },
    {
      id: 'fn-8',
      character: 'eisen',
      start: 39,
      end: 44.5,
      tokens: [
        { t: '人間', r: 'にんげん' },
        { t: 'の' },
        { t: '寿命', r: 'じゅみょう' },
        { t: 'は' },
        { t: '短', r: 'みじか' },
        { t: 'い。だからこそ、' },
        { t: '今', r: 'いま' },
        { t: 'を' },
        { t: '大切', r: 'たいせつ' },
        { t: 'にするんだ。' },
      ],
      translation: 'Human lives are short. That is exactly why we treasure the present.',
      vocab: [
        { w: '寿命', r: 'じゅみょう', en: 'lifespan' },
        { w: '大切にする', r: 'たいせつにする', en: 'to treasure, to hold dear' },
      ],
      grammar: [
        { p: 'だからこそ', en: '"precisely because of that" — emphatic reason' },
        { p: '〜んだ', en: 'explanatory ending: stating how things are' },
      ],
    },
    {
      id: 'fn-9',
      character: 'frieren',
      start: 45,
      end: 50,
      tokens: [
        { t: '私', r: 'わたし' },
        { t: '、' },
        { t: '人間', r: 'にんげん' },
        { t: 'のことをもっと' },
        { t: '知', r: 'し' },
        { t: 'ってみようと' },
        { t: '思', r: 'おも' },
        { t: 'う。' },
      ],
      translation: "I think I'll try to get to know humans better.",
      vocab: [{ w: '人間', r: 'にんげん', en: 'human being' }],
      grammar: [
        { p: '〜てみる', en: '"try doing ~" — 知ってみる = try getting to know' },
        { p: '〜ようと思う', en: '"I think I\'ll ~" — stating an intention' },
      ],
    },
    {
      id: 'fn-10',
      character: 'heiter',
      start: 50.5,
      end: 55,
      tokens: [
        { t: 'それがいい。ヒンメルもきっと' },
        { t: '喜', r: 'よろこ' },
        { t: 'びますよ。' },
      ],
      translation: "That's good. I'm sure Himmel would be glad, too.",
      vocab: [
        { w: '喜ぶ', r: 'よろこぶ', en: 'to be glad, to rejoice' },
        { w: 'きっと', en: 'surely, certainly' },
      ],
      grammar: [{ p: 'きっと〜ますよ', en: 'reassuring someone: "I\'m sure that…"' }],
    },
  ],
};

/** Frieren and Fern on the road: why collect spells? (everyday-speech practice). */
export const SCENE_FERN: SkitScript = {
  title: '葬送のフリーレン — フェルンと魔法収集 (デモ)',
  characters: [
    { id: 'frieren', name: 'フリーレン', color: '#7ecbff' },
    { id: 'fern', name: 'フェルン', color: '#f5c2e7' },
  ],
  lines: [
    {
      id: 'fe-1',
      character: 'fern',
      start: 5,
      end: 9.5,
      tokens: [
        { t: 'フリーレン' },
        { t: '様', r: 'さま' },
        { t: '、そろそろ' },
        { t: '起', r: 'お' },
        { t: 'きてください。もう' },
        { t: '昼', r: 'ひる' },
        { t: 'ですよ。' },
      ],
      translation: "Frieren-sama, it's time to wake up. It's already noon.",
      vocab: [
        { w: 'そろそろ', en: 'about time to; soon' },
        { w: '昼', r: 'ひる', en: 'noon, midday' },
      ],
      grammar: [
        { p: '〜てください', en: 'polite request: "please ~"' },
        { p: '名前＋様', en: 'honorific 様 — Fern\'s formal respect for her master' },
      ],
    },
    {
      id: 'fe-2',
      character: 'frieren',
      start: 10,
      end: 12.5,
      tokens: [
        { t: 'あと' },
        { t: '五分', r: 'ごふん' },
        { t: '…。' },
      ],
      translation: 'Five more minutes…',
      vocab: [{ w: 'あと〜', en: '"~ more" — あと五分 = five more minutes' }],
      grammar: [{ p: 'あと＋数量', en: 'remaining amount of time or things' }],
    },
    {
      id: 'fe-3',
      character: 'fern',
      start: 13,
      end: 16.5,
      tokens: [
        { t: '昨日', r: 'きのう' },
        { t: 'もそう' },
        { t: '言', r: 'い' },
        { t: 'っていました。' },
      ],
      translation: 'You said that yesterday, too.',
      vocab: [{ w: '昨日', r: 'きのう', en: 'yesterday' }],
      grammar: [
        { p: '〜ていました', en: 'was doing / used to — reporting a repeated past' },
        { p: 'そう言う', en: '"say so" — そう points back at what was said' },
      ],
    },
    {
      id: 'fe-4',
      character: 'frieren',
      start: 17,
      end: 20.5,
      tokens: [
        { t: 'フェルンは' },
        { t: '真面目', r: 'まじめ' },
        { t: 'だね。' },
      ],
      translation: "You're so diligent, Fern.",
      vocab: [{ w: '真面目', r: 'まじめ', en: 'serious, diligent' }],
      grammar: [{ p: '〜だね', en: 'friendly observation inviting agreement' }],
    },
    {
      id: 'fe-5',
      character: 'fern',
      start: 21,
      end: 25.5,
      tokens: [
        { t: 'フリーレン' },
        { t: '様', r: 'さま' },
        { t: 'は、どうして' },
        { t: '魔法', r: 'まほう' },
        { t: 'を' },
        { t: '集', r: 'あつ' },
        { t: 'めているのですか。' },
      ],
      translation: 'Why do you collect spells, Frieren-sama?',
      vocab: [
        { w: '魔法', r: 'まほう', en: 'magic, a spell' },
        { w: '集める', r: 'あつめる', en: 'to collect, to gather' },
      ],
      grammar: [
        { p: 'どうして〜のですか', en: 'polite "why…?" asking for the story behind it' },
        { p: '〜ている', en: 'ongoing habit: "have been collecting"' },
      ],
    },
    {
      id: 'fe-6',
      character: 'frieren',
      start: 26,
      end: 30.5,
      tokens: [
        { t: '趣味', r: 'しゅみ' },
        { t: 'だよ。くだらない' },
        { t: '魔法', r: 'まほう' },
        { t: 'ばかりだけどね。' },
      ],
      translation: "It's a hobby. Though they're mostly silly spells.",
      vocab: [
        { w: '趣味', r: 'しゅみ', en: 'hobby' },
        { w: 'くだらない', en: 'silly, trivial, worthless' },
      ],
      grammar: [
        { p: '〜ばかり', en: '"nothing but ~"' },
        { p: '〜だけどね', en: 'soft concession: "…though, mind you"' },
      ],
    },
    {
      id: 'fe-7',
      character: 'fern',
      start: 31,
      end: 34.5,
      tokens: [
        { t: '例', r: 'たと' },
        { t: 'えば、どんな' },
        { t: '魔法', r: 'まほう' },
        { t: 'ですか。' },
      ],
      translation: 'For example, what kind of spells?',
      vocab: [{ w: '例えば', r: 'たとえば', en: 'for example' }],
      grammar: [{ p: 'どんな＋noun', en: '"what kind of ~?"' }],
    },
    {
      id: 'fe-8',
      character: 'frieren',
      start: 35,
      end: 40.5,
      tokens: [
        { t: '服', r: 'ふく' },
        { t: 'の' },
        { t: '汚', r: 'よご' },
        { t: 'れをきれいさっぱり' },
        { t: '落', r: 'お' },
        { t: 'とす' },
        { t: '魔法', r: 'まほう' },
        { t: 'とか。' },
      ],
      translation: 'Like a spell that gets stains out of clothes, completely clean.',
      vocab: [
        { w: '汚れ', r: 'よごれ', en: 'stain, dirt' },
        { w: '落とす', r: 'おとす', en: 'to remove, to get (a stain) out' },
      ],
      grammar: [
        { p: '〜とか', en: 'casual "like ~ / such as ~"' },
        { p: 'きれいさっぱり', en: 'idiomatic emphasis: "completely, without a trace"' },
      ],
    },
    {
      id: 'fe-9',
      character: 'fern',
      start: 41,
      end: 44.5,
      tokens: [
        { t: '…' },
        { t: '意外', r: 'いがい' },
        { t: 'と' },
        { t: '便利', r: 'べんり' },
        { t: 'そうですね。' },
      ],
      translation: '…That actually sounds pretty useful.',
      vocab: [
        { w: '意外と', r: 'いがいと', en: 'surprisingly, unexpectedly' },
        { w: '便利', r: 'べんり', en: 'convenient, useful' },
      ],
      grammar: [{ p: '〜そう', en: '"looks/sounds ~" — judging from appearances' }],
    },
    {
      id: 'fe-10',
      character: 'frieren',
      start: 45,
      end: 47.5,
      tokens: [{ t: 'でしょ？' }],
      translation: 'Right?',
      vocab: [{ w: 'でしょ？', en: '"right?" — casual push for agreement' }],
      grammar: [{ p: 'でしょ？', en: 'clipped でしょう: confident "see, told you"' }],
    },
  ],
};

function shiftLines(source: SkitScript, offset: number, prefix: string): ScriptLine[] {
  return source.lines.map((line) => ({
    ...line,
    id: prefix + line.id,
    start: line.start + offset,
    end: line.end + offset,
  }));
}

function unionCharacters(sources: SkitScript[]): Character[] {
  const byId = new Map<string, Character>();
  for (const s of sources) for (const c of s.characters) if (!byId.has(c.id)) byId.set(c.id, c);
  return [...byId.values()];
}

/**
 * All three demo scenes chaptered into one script — how a full episode looks
 * once its iconic scenes are marked: jump straight to the moment (and its
 * music) you want to practice.
 */
export const SCENE_COMPILATION: SkitScript = {
  title: '葬送のフリーレン 名場面集 (デモ)',
  characters: unionCharacters([DEMO_SCRIPT, SCENE_FUNERAL, SCENE_FERN]),
  scenes: [
    { id: 'sc-1', title: '流星群の約束', start: 0, end: 66 },
    { id: 'sc-2', title: '五十年後の再会', start: 70, end: 129 },
    { id: 'sc-3', title: 'フェルンと魔法収集', start: 135, end: 186 },
  ],
  lines: [
    ...shiftLines(DEMO_SCRIPT, 0, 'c1-'),
    ...shiftLines(SCENE_FUNERAL, 65, 'c2-'),
    ...shiftLines(SCENE_FERN, 130, 'c3-'),
  ],
};

export const DEMO_SCENES: SkitScript[] = [
  DEMO_SCRIPT,
  SCENE_FUNERAL,
  SCENE_FERN,
  SCENE_COMPILATION,
];

/** Publicly linkable solo-practice pages: /#/p/<slug> */
export const PUBLIC_SCENES: { slug: string; script: SkitScript }[] = [
  { slug: 'meteor-promise', script: DEMO_SCRIPT },
  { slug: 'himmel-funeral', script: SCENE_FUNERAL },
  { slug: 'fern-magic', script: SCENE_FERN },
  { slug: 'iconic-scenes', script: SCENE_COMPILATION },
];

export function publicScene(slug: string): SkitScript | null {
  return PUBLIC_SCENES.find((p) => p.slug === slug)?.script ?? null;
}
