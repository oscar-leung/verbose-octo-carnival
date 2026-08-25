import { useState } from 'react';
import { loadName, saveName } from '../lib/settings';
import { PUBLIC_SCENES } from '../data/demoScenes';
import NightSky from './NightSky';

function randomRoomId(): string {
  return Math.random().toString(36).slice(2, 8);
}

export default function Landing() {
  const [name, setName] = useState(loadName);
  const [joinCode, setJoinCode] = useState('');
  const [joinErr, setJoinErr] = useState<string | null>(null);

  const persistName = () => {
    const trimmed = name.trim();
    if (trimmed) saveName(trimmed);
    return trimmed;
  };

  const createRoom = () => {
    if (!persistName()) {
      setJoinErr('まず名前を入れてね — enter a name first.');
      return;
    }
    location.hash = `#/r/${randomRoomId()}`;
  };

  const joinRoom = () => {
    if (!persistName()) {
      setJoinErr('まず名前を入れてね — enter a name first.');
      return;
    }
    const m = /([A-Za-z0-9-]{3,32})[^A-Za-z0-9-]*$/.exec(joinCode.trim());
    if (!m) {
      setJoinErr('That does not look like a room code or link.');
      return;
    }
    location.hash = `#/r/${m[1]?.toLowerCase()}`;
  };

  return (
    <div className="landing">
      <NightSky className="landing-sky" />
      <div className="landing-card">
        <h1 className="logo">
          Serifu <span className="logo-jp">台詞</span>
        </h1>
        <p className="hero-line">
          <ruby>
            五十年<rt>ごじゅうねん</rt>
          </ruby>
          に
          <ruby>
            一度<rt>いちど</rt>
          </ruby>
          の
          <ruby>
            流星群<rt>りゅうせいぐん</rt>
          </ruby>
          みたいな
          <ruby>
            夜<rt>よる</rt>
          </ruby>
          を。
        </p>
        <p className="tagline">
          Practice Japanese by <strong>voicing Frieren's journey</strong> with your own party —
          the episode plays in sync, the video pauses at your character's line, you say it,
          and the story rolls on. Furigana, translations, grammar notes, and voice chat included.
        </p>
        <ol className="howto">
          <li>Create a room and send the link to your party.</li>
          <li>Everyone opens their own copy of the episode (files stay on your device).</li>
          <li>Claim フリーレン, フェルン, ヒンメル… — rehearsal mode pauses at your lines,
            and speech scoring tells you how close you got.</li>
          <li>Pause anytime to talk grammar, vocab, or the feels. 単語帳 collects the words
            you meet for Anki.</li>
        </ol>
        <div className="landing-form">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="名前 / your name"
            maxLength={24}
          />
          <button className="primary" onClick={createRoom}>
            ＋ Create a room
          </button>
          <div className="row">
            <input
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
              placeholder="room code or link"
              onKeyDown={(e) => {
                if (e.key === 'Enter') joinRoom();
              }}
            />
            <button onClick={joinRoom}>Join</button>
          </div>
          {joinErr && <p className="error">{joinErr}</p>}
        </div>
        <div className="solo-links">
          <span className="bar-label">一人で練習 — solo memory practice, no room needed:</span>
          <div className="row">
            {PUBLIC_SCENES.map((p) => (
              <a key={p.slug} className="chip" href={`#/p/${p.slug}`}>
                {p.script.title.replace('葬送のフリーレン — ', '').replace('葬送のフリーレン ', '')}
              </a>
            ))}
          </div>
        </div>
        <p className="fineprint">
          Bundled Frieren practice scenes to start; import any episode's subtitles for the
          rest of the journey. No accounts, nothing uploaded — only timing and the script are
          shared with your room. <a href="/privacy.html">Privacy</a>
          {import.meta.env.VITE_SUPPORT_URL && (
            <>
              {' · '}
              <a href={import.meta.env.VITE_SUPPORT_URL} target="_blank" rel="noreferrer">
                ☕ Buy me a coffee
              </a>
            </>
          )}
        </p>
      </div>
    </div>
  );
}
