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

/** Stark scolded for dessert, then owning his fear before a fight (casual masculine speech). */
export const SCENE_STARK: SkitScript = {
  title: '葬送のフリーレン — シュタルクの覚悟 (デモ)',
  characters: [
    { id: 'stark', name: 'シュタルク', color: '#f38ba8' },
    { id: 'fern', name: 'フェルン', color: '#f5c2e7' },
    { id: 'frieren', name: 'フリーレン', color: '#7ecbff' },
  ],
  lines: [
    {
      id: 'st-1',
      character: 'fern',
      start: 5,
      end: 9.5,
      tokens: [
        { t: 'シュタルク' },
        { t: '様', r: 'さま' },
        { t: '、また' },
        { t: '甘', r: 'あま' },
        { t: 'いものを' },
        { t: '食', r: 'た' },
        { t: 'べてばかりですね。' },
      ],
      translation: "Stark-sama, you're eating nothing but sweets again.",
      vocab: [
        { w: '甘いもの', r: 'あまいもの', en: 'sweets, sweet things' },
        { w: 'また', en: 'again' },
      ],
      grammar: [
        { p: '〜てばかり', en: 'doing nothing but ~ — a mild complaint about a habit' },
      ],
    },
    {
      id: 'st-2',
      character: 'stark',
      start: 10,
      end: 14.5,
      tokens: [
        { t: '別', r: 'べつ' },
        { t: 'にいいだろ。' },
        { t: '俺', r: 'おれ' },
        { t: 'の' },
        { t: '金', r: 'かね' },
        { t: 'で' },
        { t: '買', r: 'か' },
        { t: 'ったんだし。' },
      ],
      translation: "What's the big deal? I bought it with my own money.",
      vocab: [
        { w: '別に', r: 'べつに', en: 'not particularly; (with いい) "it\'s fine, isn\'t it"' },
        { w: '俺', r: 'おれ', en: 'I, me — rough masculine first person' },
      ],
      grammar: [
        { p: '〜だろ', en: 'casual masculine "right? / isn\'t it" — clipped だろう' },
        { p: '〜し', en: 'gives a reason and trails off' },
      ],
    },
    {
      id: 'st-3',
      character: 'fern',
      start: 15,
      end: 19.5,
      tokens: [
        { t: '夕食', r: 'ゆうしょく' },
        { t: 'の' },
        { t: '前', r: 'まえ' },
        { t: 'だと' },
        { t: '言', r: 'い' },
        { t: 'ったのに。' },
      ],
      translation: 'Even though I told you it was almost dinnertime.',
      vocab: [{ w: '夕食', r: 'ゆうしょく', en: 'dinner, evening meal' }],
      grammar: [
        { p: '〜のに', en: 'reproachful "even though…" — the complaint hangs in the air' },
      ],
    },
    {
      id: 'st-4',
      character: 'frieren',
      start: 20,
      end: 24.5,
      tokens: [
        { t: '二人', r: 'ふたり' },
        { t: 'とも、やめな。' },
        { t: '魔物', r: 'まもの' },
        { t: 'が' },
        { t: '近', r: 'ちか' },
        { t: 'くにいるよ。' },
      ],
      translation: "Cut it out, you two. There's a monster nearby.",
      vocab: [
        { w: '魔物', r: 'まもの', en: 'monster, demon beast' },
        { w: '近く', r: 'ちかく', en: 'nearby, the vicinity' },
      ],
      grammar: [
        { p: '〜な (やめな)', en: 'soft command — clipped なさい: "stop it"' },
      ],
    },
    {
      id: 'st-5',
      character: 'stark',
      start: 25,
      end: 28.5,
      tokens: [
        { t: 'は？' },
        { t: '聞', r: 'き' },
        { t: 'いてないんだけど…。' },
      ],
      translation: "Huh? Nobody told me about that…",
      vocab: [{ w: '聞く', r: 'きく', en: 'to hear, to be told' }],
      grammar: [
        { p: '〜んだけど', en: 'trailing complaint: "…you know" — objecting softly' },
      ],
    },
    {
      id: 'st-6',
      character: 'frieren',
      start: 29,
      end: 33.5,
      tokens: [
        { t: 'シュタルク、' },
        { t: '前', r: 'まえ' },
        { t: 'に' },
        { t: '出', r: 'で' },
        { t: 'ろ。' },
        { t: '斧', r: 'おの' },
        { t: 'を' },
        { t: '構', r: 'かま' },
        { t: 'えて。' },
      ],
      translation: 'Stark, get up front. Ready your axe.',
      vocab: [
        { w: '斧', r: 'おの', en: 'axe' },
        { w: '構える', r: 'かまえる', en: 'to take a stance, to ready (a weapon)' },
      ],
      grammar: [
        { p: '命令形 (出ろ)', en: 'imperative form — blunt direct order: "get out (front)!"' },
      ],
    },
    {
      id: 'st-7',
      character: 'stark',
      start: 34,
      end: 38.5,
      tokens: [
        { t: '正直', r: 'しょうじき' },
        { t: '、' },
        { t: '足', r: 'あし' },
        { t: 'が' },
        { t: '震', r: 'ふる' },
        { t: 'えてるんだ。' },
      ],
      translation: "Honestly… my legs are shaking.",
      vocab: [
        { w: '正直', r: 'しょうじき', en: 'honestly, to be honest' },
        { w: '震える', r: 'ふるえる', en: 'to tremble, to shake' },
      ],
      grammar: [
        { p: '〜てる', en: 'casual contraction of 〜ている: ongoing state' },
      ],
    },
    {
      id: 'st-8',
      character: 'fern',
      start: 39,
      end: 42.5,
      tokens: [
        { t: '逃', r: 'に' },
        { t: 'げるのですか。' },
      ],
      translation: 'Are you going to run away?',
      vocab: [{ w: '逃げる', r: 'にげる', en: 'to run away, to flee' }],
      grammar: [
        { p: '〜のですか', en: 'polite question pressing for an explanation' },
      ],
    },
    {
      id: 'st-9',
      character: 'stark',
      start: 43,
      end: 48.5,
      tokens: [
        { t: 'いや。' },
        { t: '怖', r: 'こわ' },
        { t: 'いけど、やるしかない。' },
        { t: '俺', r: 'おれ' },
        { t: 'は' },
        { t: '戦士', r: 'せんし' },
        { t: 'だからな。' },
      ],
      translation: "No. I'm scared, but there's nothing to do except fight. I'm a warrior, after all.",
      vocab: [
        { w: '怖い', r: 'こわい', en: 'scary; scared' },
        { w: '戦士', r: 'せんし', en: 'warrior' },
      ],
      grammar: [
        { p: '〜しかない', en: '"have no choice but to ~" — the only option left' },
        { p: '〜からな', en: 'masculine "because, you know" — reason with bravado' },
      ],
    },
    {
      id: 'st-10',
      character: 'frieren',
      start: 49,
      end: 53.5,
      tokens: [
        { t: 'それでいい。' },
        { t: '震', r: 'ふる' },
        { t: 'えていても、' },
        { t: '前', r: 'まえ' },
        { t: 'に' },
        { t: '立', r: 'た' },
        { t: 'てるのが' },
        { t: '勇者', r: 'ゆうしゃ' },
        { t: 'だよ。' },
      ],
      translation: "That's all you need. Standing at the front even while trembling — that's what a hero is.",
      vocab: [
        { w: '勇者', r: 'ゆうしゃ', en: 'hero, brave one' },
        { w: '立つ', r: 'たつ', en: 'to stand' },
      ],
      grammar: [
        { p: '〜ていても', en: '"even while ~ing" — the state doesn\'t stop the action' },
      ],
    },
  ],
};

/** The morning of Fern's mage exam: nerves, review, and encouragement (polite vs casual). */
export const SCENE_EXAM: SkitScript = {
  title: '葬送のフリーレン — 魔法試験の朝 (デモ)',
  characters: [
    { id: 'fern', name: 'フェルン', color: '#f5c2e7' },
    { id: 'frieren', name: 'フリーレン', color: '#7ecbff' },
  ],
  lines: [
    {
      id: 'ex-1',
      character: 'fern',
      start: 5,
      end: 9.5,
      tokens: [
        { t: 'フリーレン' },
        { t: '様', r: 'さま' },
        { t: '、' },
        { t: '今日', r: 'きょう' },
        { t: 'はいよいよ' },
        { t: '試験', r: 'しけん' },
        { t: 'の' },
        { t: '日', r: 'ひ' },
        { t: 'ですね。' },
      ],
      translation: "Frieren-sama, today is finally the day of the exam.",
      vocab: [
        { w: '試験', r: 'しけん', en: 'exam, test' },
        { w: 'いよいよ', en: 'finally, at last (the moment arrives)' },
      ],
      grammar: [
        { p: '〜ですね', en: 'polite ね — sharing the moment; Fern always speaks politely' },
      ],
    },
    {
      id: 'ex-2',
      character: 'frieren',
      start: 10,
      end: 13.5,
      tokens: [
        { t: 'そうだね。' },
        { t: '緊張', r: 'きんちょう' },
        { t: 'してる？' },
      ],
      translation: 'That it is. Are you nervous?',
      vocab: [{ w: '緊張する', r: 'きんちょうする', en: 'to be nervous, to tense up' }],
      grammar: [
        { p: 'plain form＋？', en: 'casual question by intonation alone — Frieren\'s relaxed register, opposite Fern\'s polite です／ます' },
      ],
    },
    {
      id: 'ex-3',
      character: 'fern',
      start: 14,
      end: 18.5,
      tokens: [
        { t: '少', r: 'すこ' },
        { t: 'し。' },
        { t: '昨夜', r: 'ゆうべ' },
        { t: 'は' },
        { t: '考', r: 'かんが' },
        { t: 'えすぎて' },
        { t: '眠', r: 'ねむ' },
        { t: 'れませんでした。' },
      ],
      translation: "A little. Last night I thought about it too much and couldn't sleep.",
      vocab: [
        { w: '昨夜', r: 'ゆうべ', en: 'last night' },
        { w: '眠れる', r: 'ねむれる', en: 'to be able to sleep (potential form)' },
      ],
      grammar: [
        { p: '〜すぎる', en: 'to do ~ too much — 考えすぎる = overthink' },
      ],
    },
    {
      id: 'ex-4',
      character: 'frieren',
      start: 19,
      end: 23.5,
      tokens: [
        { t: '心配', r: 'しんぱい' },
        { t: 'しすぎだよ。' },
        { t: '普段', r: 'ふだん' },
        { t: '通', r: 'どお' },
        { t: 'りにやれば' },
        { t: '受', r: 'う' },
        { t: 'かるよ。' },
      ],
      translation: "You're worrying too much. If you just do it like you always do, you'll pass.",
      vocab: [
        { w: '普段通り', r: 'ふだんどおり', en: 'as usual, the way one always does' },
        { w: '受かる', r: 'うかる', en: 'to pass (an exam)' },
      ],
      grammar: [
        { p: '〜ば', en: 'conditional: "if you do ~, then…" — やれば受かる' },
        { p: '〜すぎ', en: 'noun form of すぎる: "too much (worrying)"' },
      ],
    },
    {
      id: 'ex-5',
      character: 'fern',
      start: 24,
      end: 28.5,
      tokens: [
        { t: 'もう' },
        { t: '一度', r: 'いちど' },
        { t: 'だけ、' },
        { t: '防御', r: 'ぼうぎょ' },
        { t: '魔法', r: 'まほう' },
        { t: 'の' },
        { t: '復習', r: 'ふくしゅう' },
        { t: 'をしてもいいですか。' },
      ],
      translation: 'May I review the defensive spells just one more time?',
      vocab: [
        { w: '復習', r: 'ふくしゅう', en: 'review (of what one has studied)' },
        { w: '防御', r: 'ぼうぎょ', en: 'defense' },
      ],
      grammar: [
        { p: '〜てもいいですか', en: 'polite request for permission: "may I ~?"' },
      ],
    },
    {
      id: 'ex-6',
      character: 'frieren',
      start: 29,
      end: 33.5,
      tokens: [
        { t: 'いいよ。じゃあ、' },
        { t: '忘', r: 'わす' },
        { t: 'れないように' },
        { t: '一番', r: 'いちばん' },
        { t: '大事', r: 'だいじ' },
        { t: 'なところだけね。' },
      ],
      translation: "Sure. Then just the most important part, so you don't forget it.",
      vocab: [
        { w: '忘れる', r: 'わすれる', en: 'to forget' },
        { w: '大事', r: 'だいじ', en: 'important' },
      ],
      grammar: [
        { p: '〜ないように', en: '"so that ~ not happen" — purpose: so you don\'t forget' },
      ],
    },
    {
      id: 'ex-7',
      character: 'fern',
      start: 34,
      end: 38.5,
      tokens: [
        { t: 'もし' },
        { t: '落', r: 'お' },
        { t: 'ちたら、どうすれば' },
        { t: 'いいのでしょうか。' },
      ],
      translation: 'If I fail… what should I do?',
      vocab: [{ w: '落ちる', r: 'おちる', en: 'to fail (an exam); to fall' }],
      grammar: [
        { p: 'どうすればいい', en: '"what should (I) do?" — ば conditional inside a set phrase' },
      ],
    },
    {
      id: 'ex-8',
      character: 'frieren',
      start: 39,
      end: 43.5,
      tokens: [
        { t: '大丈夫', r: 'だいじょうぶ' },
        { t: '。フェルンなら' },
        { t: '大丈夫', r: 'だいじょうぶ' },
        { t: 'だよ。' },
      ],
      translation: "It's fine. If it's you, Fern, you'll be fine.",
      vocab: [{ w: '大丈夫', r: 'だいじょうぶ', en: 'all right, fine, no problem' }],
      grammar: [
        { p: '〜なら大丈夫', en: 'classic reassurance: "if it\'s you, it\'ll be okay"' },
      ],
    },
    {
      id: 'ex-9',
      character: 'frieren',
      start: 44,
      end: 48.5,
      tokens: [
        { t: '合格', r: 'ごうかく' },
        { t: 'できるように、' },
        { t: '私', r: 'わたし' },
        { t: 'も' },
        { t: '祈', r: 'いの' },
        { t: 'っておくよ。' },
      ],
      translation: "I'll be hoping you pass, too.",
      vocab: [
        { w: '合格', r: 'ごうかく', en: 'passing (an exam)' },
        { w: '祈る', r: 'いのる', en: 'to pray, to hope' },
      ],
      grammar: [
        { p: '〜ように (祈る)', en: 'hope/wish: "praying that ~ comes true"' },
        { p: '〜ておく', en: 'do in advance / keep doing for later' },
      ],
    },
    {
      id: 'ex-10',
      character: 'fern',
      start: 49,
      end: 53.5,
      tokens: [
        { t: 'はい。' },
        { t: '行', r: 'い' },
        { t: 'ってまいります、フリーレン' },
        { t: '様', r: 'さま' },
        { t: '。' },
      ],
      translation: "Yes. I'm off, Frieren-sama.",
      vocab: [
        { w: '行ってまいります', r: 'いってまいります', en: 'humble "I\'m off" — formal 行ってきます' },
      ],
      grammar: [
        { p: '〜てまいります', en: 'humble form of 〜ていきます — extra-polite leave-taking' },
      ],
    },
  ],
};

/** Flashback: Himmel coaxes Frieren into showing the flower-field spell she loves. */
export const SCENE_FLOWER_FIELD: SkitScript = {
  title: '葬送のフリーレン — 花畑の魔法 (デモ)',
  characters: [
    { id: 'frieren', name: 'フリーレン', color: '#7ecbff' },
    { id: 'himmel', name: 'ヒンメル', color: '#b4befe' },
  ],
  lines: [
    {
      id: 'hb-1',
      character: 'himmel',
      start: 5,
      end: 9.5,
      tokens: [
        { t: 'フリーレン、あの' },
        { t: '花畑', r: 'はなばたけ' },
        { t: 'を' },
        { t: '出', r: 'だ' },
        { t: 'す' },
        { t: '魔法', r: 'まほう' },
        { t: '、' },
        { t: '見', r: 'み' },
        { t: 'せてくれない？' },
      ],
      translation: "Frieren, won't you show me that spell that makes a field of flowers?",
      vocab: [
        { w: '花畑', r: 'はなばたけ', en: 'field of flowers' },
        { w: '見せる', r: 'みせる', en: 'to show' },
      ],
      grammar: [
        { p: '〜てくれない？', en: 'casual request: "won\'t you do ~ for me?" — くれる marks the action as done for the speaker' },
      ],
    },
    {
      id: 'hb-2',
      character: 'frieren',
      start: 10,
      end: 14.5,
      tokens: [
        { t: '別', r: 'べつ' },
        { t: 'に…。' },
        { t: '大', r: 'たい' },
        { t: 'した' },
        { t: '魔法', r: 'まほう' },
        { t: 'じゃないよ。' },
      ],
      translation: "It's nothing… It's not that great a spell.",
      vocab: [
        { w: '別に', r: 'べつに', en: '"not really…" — embarrassed brush-off' },
        { w: '大した', r: 'たいした', en: 'great, much of a (with a negative)' },
      ],
      grammar: [
        { p: '別に…', en: 'classic 照れ deflection — playing something down when shy' },
        { p: '大した＋noun＋negative', en: '"not much of a ~" — modest downgrading' },
      ],
    },
    {
      id: 'hb-3',
      character: 'himmel',
      start: 15,
      end: 19.5,
      tokens: [
        { t: 'でも' },
        { t: '君', r: 'きみ' },
        { t: 'は、その' },
        { t: '魔法', r: 'まほう' },
        { t: 'を' },
        { t: '使', r: 'つか' },
        { t: 'うのが' },
        { t: '好', r: 'す' },
        { t: 'きなんだろう？' },
      ],
      translation: 'But you love using that spell, don\'t you?',
      vocab: [{ w: '君', r: 'きみ', en: 'you — warm, familiar second person' }],
      grammar: [
        { p: '〜のが好き', en: 'verb + のが好き: "like doing ~" — の turns the verb into a noun' },
      ],
    },
    {
      id: 'hb-4',
      character: 'frieren',
      start: 20,
      end: 24.5,
      tokens: [
        { t: '…もし' },
        { t: '笑', r: 'わら' },
        { t: 'われたら、どうするの。' },
      ],
      translation: '…And if I got laughed at, what then?',
      vocab: [{ w: '笑う', r: 'わらう', en: 'to laugh (笑われる = to be laughed at)' }],
      grammar: [
        { p: '〜たら', en: '"if/when ~" conditional: 笑われたら = if I get laughed at' },
        { p: 'もし〜', en: 'flags a hypothetical — pairs with たら/ば' },
      ],
    },
    {
      id: 'hb-5',
      character: 'himmel',
      start: 25,
      end: 29.5,
      tokens: [
        { t: '笑', r: 'わら' },
        { t: 'わないよ。なんなら、' },
        { t: '約束', r: 'やくそく' },
        { t: 'してあげる。' },
      ],
      translation: "I won't laugh. I'll even promise you that.",
      vocab: [
        { w: '約束する', r: 'やくそくする', en: 'to promise' },
        { w: 'なんなら', en: '"if you like, I could even…"' },
      ],
      grammar: [
        { p: '〜てあげる', en: '"do ~ for someone" — the mirror of てくれる, from the giver\'s side' },
      ],
    },
    {
      id: 'hb-6',
      character: 'frieren',
      start: 30,
      end: 34.5,
      tokens: [
        { t: '…わかった。' },
        { t: '少', r: 'すこ' },
        { t: 'しだけだよ。' },
      ],
      translation: '…Fine. Just a little, okay?',
      vocab: [{ w: '少し', r: 'すこし', en: 'a little' }],
      grammar: [
        { p: 'わかった', en: 'plain-form "got it / fine" — casual reluctant agreement' },
      ],
    },
    {
      id: 'hb-7',
      character: 'himmel',
      start: 35,
      end: 39.5,
      tokens: [
        { t: 'わあ…きれいだなあ。まるで' },
        { t: '春', r: 'はる' },
        { t: 'が' },
        { t: '来', r: 'き' },
        { t: 'たみたいだ。' },
      ],
      translation: "Wow… it's beautiful. It's just like spring has come.",
      vocab: [
        { w: 'まるで', en: 'just like, as if' },
        { w: '春', r: 'はる', en: 'spring' },
      ],
      grammar: [
        { p: 'まるで〜みたい', en: '"exactly like ~" — まるで strengthens the comparison' },
      ],
    },
    {
      id: 'hb-8',
      character: 'frieren',
      start: 40,
      end: 44.5,
      tokens: [
        { t: 'そんなに' },
        { t: '嬉', r: 'うれ' },
        { t: 'しそうな' },
        { t: '顔', r: 'かお' },
        { t: '、' },
        { t: '初', r: 'はじ' },
        { t: 'めて' },
        { t: '見', r: 'み' },
        { t: 'た。' },
      ],
      translation: "That's the first time I've seen you look so happy.",
      vocab: [
        { w: '嬉しい', r: 'うれしい', en: 'happy, glad' },
        { w: '初めて', r: 'はじめて', en: 'for the first time' },
      ],
      grammar: [
        { p: 'adjective stem＋そう', en: '"looks ~" from appearance: 嬉しそう = looks happy' },
      ],
    },
    {
      id: 'hb-9',
      character: 'himmel',
      start: 45,
      end: 49.5,
      tokens: [
        { t: 'こんなに' },
        { t: '素敵', r: 'すてき' },
        { t: 'な' },
        { t: '魔法', r: 'まほう' },
        { t: 'なんだから、' },
        { t: '胸', r: 'むね' },
        { t: 'を' },
        { t: '張', r: 'は' },
        { t: 'って' },
        { t: '見', r: 'み' },
        { t: 'せるといいよ。' },
      ],
      translation: "It's such a lovely spell — you should show it with your head held high.",
      vocab: [
        { w: '素敵', r: 'すてき', en: 'lovely, wonderful' },
        { w: '胸を張る', r: 'むねをはる', en: 'to stand tall, to be proud (lit. puff out one\'s chest)' },
      ],
      grammar: [
        { p: '〜といい', en: 'gentle suggestion: "it\'d be good if you ~ / you should ~"' },
      ],
    },
    {
      id: 'hb-10',
      character: 'frieren',
      start: 50,
      end: 54.5,
      tokens: [
        { t: '…ありがとう、ヒンメル。ちょっとだけ、' },
        { t: '自慢', r: 'じまん' },
        { t: 'の' },
        { t: '魔法', r: 'まほう' },
        { t: 'になった。' },
      ],
      translation: '…Thank you, Himmel. Now it\'s become, just a little, a spell I\'m proud of.',
      vocab: [{ w: '自慢', r: 'じまん', en: 'pride; something to boast of (自慢の〜 = one\'s prized ~)' }],
      grammar: [
        { p: 'noun＋になる', en: 'change of state: "become ~" — になった = has become' },
      ],
    },
  ],
};

/** Packing to depart: Stark overpacked food, Fern scolds, Frieren wants a detour. */
export const SCENE_JOURNEY_PREP: SkitScript = {
  title: '葬送のフリーレン — 旅の準備 (デモ)',
  characters: [
    { id: 'fern', name: 'フェルン', color: '#f5c2e7' },
    { id: 'stark', name: 'シュタルク', color: '#f38ba8' },
    { id: 'frieren', name: 'フリーレン', color: '#7ecbff' },
  ],
  lines: [
    {
      id: 'tp-1',
      character: 'fern',
      start: 5,
      end: 9.5,
      tokens: [
        { t: 'シュタルク' },
        { t: '様', r: 'さま' },
        { t: '、その' },
        { t: '荷物', r: 'にもつ' },
        { t: '、' },
        { t: '多', r: 'おお' },
        { t: 'すぎませんか。' },
      ],
      translation: "Stark-sama, isn't that way too much luggage?",
      vocab: [
        { w: '荷物', r: 'にもつ', en: 'luggage, baggage' },
        { w: '多い', r: 'おおい', en: 'many, a lot' },
      ],
      grammar: [
        { p: '〜すぎる', en: 'excess: "too ~" — 多すぎる = too much' },
        { p: '〜ませんか', en: 'polite negative question — a soft way to criticize' },
      ],
    },
    {
      id: 'tp-2',
      character: 'stark',
      start: 10,
      end: 14.5,
      tokens: [
        { t: '食', r: 'た' },
        { t: 'べ' },
        { t: '物', r: 'もの' },
        { t: 'は' },
        { t: '大事', r: 'だいじ' },
        { t: 'だろ。パンを' },
        { t: '十個', r: 'じゅっこ' },
        { t: 'も' },
        { t: '買', r: 'か' },
        { t: 'ったんだ。' },
      ],
      translation: 'Food matters, right? I bought a whole ten loaves of bread.',
      vocab: [
        { w: '〜個', r: 'こ', en: 'counter for small objects (十個 = ten of them)' },
        { w: '食べ物', r: 'たべもの', en: 'food' },
      ],
      grammar: [
        { p: '数量＋も', en: '"as many as ~" — も marks the amount as surprisingly large' },
        { p: '〜だろ', en: 'rough casual "right?" — contrast with Fern\'s polite です／ます' },
      ],
    },
    {
      id: 'tp-3',
      character: 'fern',
      start: 15,
      end: 19.5,
      tokens: [
        { t: '二', r: 'ふた' },
        { t: 'つで' },
        { t: '十分', r: 'じゅうぶん' },
        { t: 'です。' },
        { t: '荷物', r: 'にもつ' },
        { t: 'は' },
        { t: '軽', r: 'かる' },
        { t: 'いほうがいいですよ。' },
      ],
      translation: 'Two is plenty. Lighter luggage is better, you know.',
      vocab: [
        { w: '十分', r: 'じゅうぶん', en: 'enough, sufficient' },
        { w: '軽い', r: 'かるい', en: 'light (in weight)' },
      ],
      grammar: [
        { p: '〜つ', en: 'native counter for things: 一つ、二つ… up to ten' },
        { p: '〜ほうがいい', en: '"~ is better / you\'d better ~"' },
      ],
    },
    {
      id: 'tp-4',
      character: 'stark',
      start: 20,
      end: 24.5,
      tokens: [
        { t: 'でも、' },
        { t: '腹', r: 'はら' },
        { t: 'が' },
        { t: '減', r: 'へ' },
        { t: 'ったら' },
        { t: '戦', r: 'たたか' },
        { t: 'えないんだけど…。' },
      ],
      translation: "But if I get hungry I can't fight, you know…",
      vocab: [
        { w: '腹が減る', r: 'はらがへる', en: 'to get hungry — rough masculine phrasing' },
        { w: '戦う', r: 'たたかう', en: 'to fight' },
      ],
      grammar: [
        { p: '可能形＋ない', en: 'negative potential: 戦えない = can\'t fight' },
      ],
    },
    {
      id: 'tp-5',
      character: 'frieren',
      start: 25,
      end: 29.5,
      tokens: [
        { t: 'ねえ、' },
        { t: '途中', r: 'とちゅう' },
        { t: 'の' },
        { t: '町', r: 'まち' },
        { t: 'で' },
        { t: '魔導書', r: 'まどうしょ' },
        { t: 'を' },
        { t: '探', r: 'さが' },
        { t: 'してもいい？' },
      ],
      translation: 'Hey, can I look for a grimoire in a town along the way?',
      vocab: [
        { w: '途中', r: 'とちゅう', en: 'on the way, en route' },
        { w: '魔導書', r: 'まどうしょ', en: 'grimoire, book of magic' },
        { w: '探す', r: 'さがす', en: 'to look for' },
      ],
      grammar: [
        { p: '〜てもいい？', en: 'casual permission: "is it okay if I ~?" — polite version is 〜てもいいですか' },
      ],
    },
    {
      id: 'tp-6',
      character: 'fern',
      start: 30,
      end: 34.5,
      tokens: [
        { t: 'だめです。' },
        { t: '日', r: 'ひ' },
        { t: 'が' },
        { t: '暮', r: 'く' },
        { t: 'れる' },
        { t: '前', r: 'まえ' },
        { t: 'に' },
        { t: '村', r: 'むら' },
        { t: 'に' },
        { t: '着', r: 'つ' },
        { t: 'かなければなりません。' },
      ],
      translation: 'No. We must reach the village before the sun goes down.',
      vocab: [
        { w: '日が暮れる', r: 'ひがくれる', en: 'the sun sets, night falls' },
        { w: '着く', r: 'つく', en: 'to arrive' },
      ],
      grammar: [
        { p: '〜なければなりません', en: 'formal obligation: "must ~ / have to ~"' },
        { p: '〜前に', en: '"before ~ing" — dictionary form + 前に' },
      ],
    },
    {
      id: 'tp-7',
      character: 'frieren',
      start: 35,
      end: 39.5,
      tokens: [
        { t: 'じゃあ、' },
        { t: '帰', r: 'かえ' },
        { t: 'りに' },
        { t: '寄', r: 'よ' },
        { t: 'らなきゃね。' },
      ],
      translation: "Then we'll just have to stop by on the way back.",
      vocab: [
        { w: '帰り', r: 'かえり', en: 'the way back, return trip' },
        { w: '寄る', r: 'よる', en: 'to stop by, to drop in' },
      ],
      grammar: [
        { p: '〜なきゃ', en: 'casual contraction of なければならない — same obligation, relaxed register' },
      ],
    },
    {
      id: 'tp-8',
      character: 'stark',
      start: 40,
      end: 44.5,
      tokens: [
        { t: '本', r: 'ほん' },
        { t: 'より' },
        { t: '飯', r: 'めし' },
        { t: 'のほうが' },
        { t: '大事', r: 'だいじ' },
        { t: 'だと' },
        { t: '思', r: 'おも' },
        { t: 'うけどなあ。' },
      ],
      translation: 'Food matters more than books, if you ask me…',
      vocab: [
        { w: '飯', r: 'めし', en: 'food, a meal — rough masculine word for ご飯' },
      ],
      grammar: [
        { p: 'AよりBのほうが', en: 'comparison: "B more than A" — 本より飯のほうが大事' },
        { p: '〜けどなあ', en: 'trailing "though…" — grumbling opinion left hanging' },
      ],
    },
    {
      id: 'tp-9',
      character: 'fern',
      start: 45,
      end: 49.5,
      tokens: [
        { t: 'どちらも' },
        { t: '大事', r: 'だいじ' },
        { t: 'です。パンは' },
        { t: '五個', r: 'ごこ' },
        { t: 'だけ' },
        { t: '持', r: 'も' },
        { t: 'って' },
        { t: '行', r: 'い' },
        { t: 'きましょう。' },
      ],
      translation: "They're both important. Let's take just five loaves.",
      vocab: [
        { w: 'どちらも', en: 'both (of two)' },
        { w: '持って行く', r: 'もっていく', en: 'to take along, to bring (away from here)' },
      ],
      grammar: [
        { p: '〜ましょう', en: 'polite "let\'s ~" — Fern stays です／ます even while compromising' },
      ],
    },
    {
      id: 'tp-10',
      character: 'frieren',
      start: 50,
      end: 54.5,
      tokens: [
        { t: '決', r: 'き' },
        { t: 'まりだね。じゃあ、' },
        { t: '出発', r: 'しゅっぱつ' },
        { t: 'しよう。' },
      ],
      translation: "It's settled, then. All right, let's set out.",
      vocab: [
        { w: '決まり', r: 'きまり', en: 'settled, a done deal' },
        { w: '出発', r: 'しゅっぱつ', en: 'departure' },
      ],
      grammar: [
        { p: '〜しよう', en: 'casual volitional "let\'s ~" — the plain twin of 〜ましょう' },
      ],
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
  SCENE_STARK,
  SCENE_EXAM,
  SCENE_FLOWER_FIELD,
  SCENE_JOURNEY_PREP,
  SCENE_COMPILATION,
];

/** Publicly linkable solo-practice pages: /#/p/<slug> */
export const PUBLIC_SCENES: { slug: string; script: SkitScript }[] = [
  { slug: 'meteor-promise', script: DEMO_SCRIPT },
  { slug: 'himmel-funeral', script: SCENE_FUNERAL },
  { slug: 'fern-magic', script: SCENE_FERN },
  { slug: 'stark-resolve', script: SCENE_STARK },
  { slug: 'exam-morning', script: SCENE_EXAM },
  { slug: 'flower-field', script: SCENE_FLOWER_FIELD },
  { slug: 'journey-prep', script: SCENE_JOURNEY_PREP },
  { slug: 'iconic-scenes', script: SCENE_COMPILATION },
];

export function publicScene(slug: string): SkitScript | null {
  return PUBLIC_SCENES.find((p) => p.slug === slug)?.script ?? null;
}
