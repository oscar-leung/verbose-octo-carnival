import { useState } from 'react';
import { loadName, saveName } from '../lib/settings';

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
      <div className="landing-card">
        <h1 className="logo">
          Serifu <span className="logo-jp">台詞</span>
        </h1>
        <p className="tagline">
          Practice Japanese by <strong>voicing your favorite anime scenes</strong> with friends —
          synced video, a timed script with furigana, character roles, and voice chat.
        </p>
        <ol className="howto">
          <li>Create a room, send the link to your friends.</li>
          <li>Everyone opens their own copy of the episode (a local video file).</li>
          <li>Claim a character. In rehearsal mode the video pauses right at your line —
            say it out loud, then continue and hear the real delivery.</li>
          <li>Pause anytime to talk about grammar, vocab, or how good Himmel looks.</li>
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
        <p className="fineprint">
          No accounts, nothing uploaded — video files stay on your device; only timing and the
          script are shared with your room.
        </p>
      </div>
    </div>
  );
}
