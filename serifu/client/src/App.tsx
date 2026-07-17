import { useEffect, useState } from 'react';
import Landing from './components/Landing';
import Room from './components/Room';
import { loadName, saveName } from './lib/settings';

function parseRoomFromHash(hash: string): string | null {
  const m = /^#\/r\/([A-Za-z0-9-]{3,32})$/.exec(hash);
  return m?.[1]?.toLowerCase() ?? null;
}

export default function App() {
  const [roomId, setRoomId] = useState<string | null>(() => parseRoomFromHash(location.hash));

  useEffect(() => {
    const onHashChange = () => setRoomId(parseRoomFromHash(location.hash));
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  if (!roomId) return <Landing />;
  return <RoomGate roomId={roomId} />;
}

function RoomGate({ roomId }: { roomId: string }) {
  const [name, setName] = useState(loadName);
  const [draft, setDraft] = useState('');
  const [entered, setEntered] = useState(() => loadName().length > 0);

  if (!entered) {
    return (
      <div className="landing">
        <div className="landing-card">
          <h1 className="logo">
            Serifu <span className="logo-jp">台詞</span>
          </h1>
          <p>Joining room <code>{roomId}</code> — what should we call you?</p>
          <form
            className="row"
            onSubmit={(e) => {
              e.preventDefault();
              const trimmed = draft.trim();
              if (!trimmed) return;
              saveName(trimmed);
              setName(trimmed);
              setEntered(true);
            }}
          >
            <input
              autoFocus
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="名前 / your name"
              maxLength={24}
            />
            <button type="submit" className="primary">
              Join
            </button>
          </form>
        </div>
      </div>
    );
  }

  return <Room roomId={roomId} name={name} />;
}
