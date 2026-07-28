import type { SkitScript } from '../../../shared/types';

/**
 * Demo skit: a short, approximate recreation of the "meteor shower promise"
 * moment from Frieren episode 1, for trying the app before importing real
 * subtitles. Timestamps are placeholders — use the editor's shift tool or
 * your personal sync offset to line them up with your copy of the episode.
 */
export const DEMO_SCRIPT: SkitScript = {
  title: '葬送のフリーレン 第1話 — 流星群の約束 (デモ)',
  characters: [
    { id: 'frieren', name: 'フリーレン', color: '#7ecbff' },
    { id: 'himmel', name: 'ヒンメル', color: '#b4befe' },
    { id: 'heiter', name: 'ハイター', color: '#a6e3a1' },
    { id: 'eisen', name: 'アイゼン', color: '#ffb86c' },
  ],
  lines: [
    {
      id: 'demo-1',
      character: 'heiter',
      start: 5,
      end: 9,
      tokens: [
        { t: '王都', r: 'おうと' },
        { t: 'は' },
        { t: '今日', r: 'きょう' },
        { t: 'もにぎやかですね。' },
      ],
      translation: 'The capital is lively today, too.',
      vocab: [
        { w: '王都', r: 'おうと', en: 'royal capital' },
        { w: 'にぎやか', en: 'lively, bustling' },
      ],
      grammar: [
        { p: '今日「も」', en: '„also/even" — today too, implying it is always like this' },
        { p: '〜ですね', en: 'soft sentence ending inviting agreement: "…, isn\'t it?"' },
      ],
    },
    {
      id: 'demo-2',
      character: 'himmel',
      start: 9.5,
      end: 14,
      tokens: [
        { t: '十年間', r: 'じゅうねんかん' },
        { t: 'の' },
        { t: '冒険', r: 'ぼうけん' },
        { t: 'も、これで' },
        { t: '終', r: 'お' },
        { t: 'わりだな。' },
      ],
      translation: 'Ten years of adventure, and this is where it ends.',
      vocab: [
        { w: '冒険', r: 'ぼうけん', en: 'adventure' },
        { w: '終わり', r: 'おわり', en: 'the end' },
      ],
      grammar: [
        { p: '十年「間」', en: 'duration suffix 〜間: "for ten years"' },
        { p: 'これで', en: '"with this" — marks something coming to a close' },
        { p: '〜だな', en: 'reflective masculine ending — half talking to oneself' },
      ],
    },
    {
      id: 'demo-3',
      character: 'frieren',
      start: 14.5,
      end: 18.5,
      tokens: [
        { t: 'たった' },
        { t: '十年', r: 'じゅうねん' },
        { t: 'だよ。あっという' },
        { t: '間', r: 'ま' },
        { t: 'だった。' },
      ],
      translation: 'It was only ten years. It went by in the blink of an eye.',
      vocab: [
        { w: 'たった', en: 'merely, only (downplays an amount)' },
        { w: 'あっという間', r: 'あっというま', en: 'in the blink of an eye' },
      ],
      grammar: [
        { p: 'たった＋数量', en: 'たった before a quantity: "just/only ten years"' },
        { p: '〜だった', en: 'plain past of だ — casual "it was"' },
      ],
    },
    {
      id: 'demo-4',
      character: 'eisen',
      start: 19,
      end: 23,
      tokens: [
        { t: '俺', r: 'おれ' },
        { t: 'たちには' },
        { t: '長', r: 'なが' },
        { t: 'い' },
        { t: '十年', r: 'じゅうねん' },
        { t: 'だったぞ。' },
      ],
      translation: 'For the rest of us, it was a long ten years.',
      vocab: [
        { w: '俺', r: 'おれ', en: 'I (rough, masculine)' },
        { w: '長い', r: 'ながい', en: 'long' },
      ],
      grammar: [
        { p: '〜には', en: 'に＋は: "for (us)" — marks whose perspective it is' },
        { p: '〜ぞ', en: 'emphatic masculine particle — adds force' },
      ],
    },
    {
      id: 'demo-5',
      character: 'himmel',
      start: 23.5,
      end: 29,
      tokens: [
        { t: 'フリーレンにとっては' },
        { t: '短', r: 'みじか' },
        { t: 'いんだろうね。エルフだから。' },
      ],
      translation: "I suppose it feels short to you, Frieren. You're an elf, after all.",
      vocab: [
        { w: '短い', r: 'みじかい', en: 'short' },
        { w: 'エルフ', en: 'elf' },
      ],
      grammar: [
        { p: '〜にとっては', en: '"from the standpoint of ~" — a key N3 pattern' },
        { p: '〜んだろうね', en: 'conjecture + agreement: "I suppose…, right?"' },
        { p: '〜だから', en: 'reason at the end: "because (you\'re an elf)"' },
      ],
    },
    {
      id: 'demo-6',
      character: 'frieren',
      start: 29.5,
      end: 32,
      tokens: [{ t: 'まあね。' }],
      translation: 'I suppose so.',
      vocab: [{ w: 'まあね', en: '"I guess / sort of" — noncommittal agreement' }],
      grammar: [
        { p: 'まあ＋ね', en: 'casual hedge まあ + agreement ね: acknowledging without committing' },
      ],
    },
    {
      id: 'demo-7',
      character: 'heiter',
      start: 32.5,
      end: 38.5,
      tokens: [
        { t: 'そういえば、' },
        { t: '今夜', r: 'こんや' },
        { t: 'は' },
        { t: '五十年', r: 'ごじゅうねん' },
        { t: 'に' },
        { t: '一度', r: 'いちど' },
        { t: 'の' },
        { t: '流星群', r: 'りゅうせいぐん' },
        { t: 'が' },
        { t: '見', r: 'み' },
        { t: 'えるそうですよ。' },
      ],
      translation:
        'Come to think of it, tonight you can see the meteor shower that comes once every fifty years.',
      vocab: [
        { w: '流星群', r: 'りゅうせいぐん', en: 'meteor shower' },
        { w: '今夜', r: 'こんや', en: 'tonight' },
        { w: '一度', r: 'いちど', en: 'once, one time' },
      ],
      grammar: [
        { p: '〜に一度', en: 'frequency: "once every ~" (五十年に一度 = once in fifty years)' },
        { p: '〜そうですよ', en: 'hearsay そうだ: "I hear that…" — reporting what others say' },
        { p: 'そういえば', en: '"come to think of it" — natural topic shift' },
      ],
    },
    {
      id: 'demo-8',
      character: 'himmel',
      start: 39,
      end: 43.5,
      tokens: [
        { t: 'それは' },
        { t: '見事', r: 'みごと' },
        { t: 'な' },
        { t: '眺', r: 'なが' },
        { t: 'めだろうな。みんなで' },
        { t: '見', r: 'み' },
        { t: 'よう。' },
      ],
      translation: "That must be a magnificent sight. Let's all watch it together.",
      vocab: [
        { w: '見事', r: 'みごと', en: 'magnificent, splendid' },
        { w: '眺め', r: 'ながめ', en: 'view, sight' },
      ],
      grammar: [
        { p: '〜だろうな', en: 'conjecture だろう + な: "it must be…, surely"' },
        { p: '見「よう」', en: 'volitional 〜よう: "let\'s watch"' },
        { p: 'みんな「で」', en: 'で marks the group doing it together' },
      ],
    },
    {
      id: 'demo-9',
      character: 'frieren',
      start: 44,
      end: 49.5,
      tokens: [
        { t: '五十年後', r: 'ごじゅうねんご' },
        { t: '、もっといい' },
        { t: '場所', r: 'ばしょ' },
        { t: 'に' },
        { t: '案内', r: 'あんない' },
        { t: 'するよ。' },
      ],
      translation: "In fifty years, I'll guide you somewhere with an even better view.",
      vocab: [
        { w: '案内する', r: 'あんないする', en: 'to guide, to show around' },
        { w: '場所', r: 'ばしょ', en: 'place, spot' },
      ],
      grammar: [
        { p: '〜後', en: 'suffix 〜後(ご): "~ later" (五十年後 = fifty years later)' },
        { p: 'もっと＋いい', en: 'もっと before an adjective: "even better"' },
      ],
    },
    {
      id: 'demo-10',
      character: 'himmel',
      start: 50,
      end: 54.5,
      tokens: [
        { t: '五十年後', r: 'ごじゅうねんご' },
        { t: 'か。' },
        { t: '僕', r: 'ぼく' },
        { t: 'はもうおじいちゃんだ。' },
      ],
      translation: "Fifty years, huh. I'll be an old man by then.",
      vocab: [
        { w: '僕', r: 'ぼく', en: 'I (gentle, masculine)' },
        { w: 'おじいちゃん', en: 'grandpa; an old man' },
      ],
      grammar: [
        { p: '〜か。', en: 'sentence-final か as musing to oneself, not a question' },
        { p: 'もう', en: '"already / by then" — もうおじいちゃんだ = I\'ll already be old' },
      ],
    },
    {
      id: 'demo-11',
      character: 'frieren',
      start: 55,
      end: 58.5,
      tokens: [
        { t: 'ヒンメルなら' },
        { t: '大丈夫', r: 'だいじょうぶ' },
        { t: 'だよ。' },
      ],
      translation: "You'll be fine, Himmel.",
      vocab: [{ w: '大丈夫', r: 'だいじょうぶ', en: 'fine, all right' }],
      grammar: [
        { p: '〜なら', en: 'conditional "if it\'s ~": ヒンメルなら = if it\'s you, Himmel' },
        { p: '〜だよ', en: 'assertive よ: gently informing/reassuring' },
      ],
    },
    {
      id: 'demo-12',
      character: 'eisen',
      start: 59,
      end: 62,
      tokens: [
        { t: '約束', r: 'やくそく' },
        { t: 'だな。' },
      ],
      translation: "It's a promise, then.",
      vocab: [{ w: '約束', r: 'やくそく', en: 'promise' }],
      grammar: [
        { p: '名詞＋だな', en: 'noun + だな: confirming with feeling — "it\'s a promise, then"' },
      ],
    },
  ],
};
