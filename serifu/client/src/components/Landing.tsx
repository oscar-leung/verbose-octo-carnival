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
          Watch together, <strong>speak your character's lines</strong> — the video pauses at
          your line and rolls on when you nail it.
        </p>
        {import.meta.env.VITE_STATIC_DEMO ? (
          <p className="muted">⚠️ Static demo — rooms need the full app. Solo scenes below work fully.</p>
        ) : (
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
        )}
        <div className="solo-links">
          <span className="bar-label">一人で練習 — solo practice:</span>
          <div className="row">
            {PUBLIC_SCENES.map((p) => (
              <a key={p.slug} className="chip" href={`#/p/${p.slug}`}>
                {p.script.title.replace('葬送のフリーレン — ', '').replace('葬送のフリーレン ', '')}
              </a>
            ))}
          </div>
        </div>
        <p className="fineprint">
          No accounts. Your videos stay on your device. <a href="guide/">Guides</a>
          {' · '}
          <a href="privacy.html">Privacy</a>
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
