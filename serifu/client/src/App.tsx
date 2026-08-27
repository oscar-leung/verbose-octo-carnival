import { useEffect, useState } from 'react';
import Landing from './components/Landing';
import Room from './components/Room';
import SoloPractice from './components/SoloPractice';
import { publicScene } from './data/demoScenes';
import { loadName, saveName } from './lib/settings';

type Route = { kind: 'landing' } | { kind: 'room'; roomId: string } | { kind: 'solo'; slug: string };

function parseRoute(hash: string): Route {
  const room = /^#\/r\/([A-Za-z0-9-]{3,32})$/.exec(hash);
  if (room?.[1]) return { kind: 'room', roomId: room[1].toLowerCase() };
  const solo = /^#\/p\/([A-Za-z0-9-]{1,64})$/.exec(hash);
  if (solo?.[1]) return { kind: 'solo', slug: solo[1].toLowerCase() };
  return { kind: 'landing' };
}

export default function App() {
  const [route, setRoute] = useState<Route>(() => parseRoute(location.hash));

  useEffect(() => {
    const onHashChange = () => setRoute(parseRoute(location.hash));
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  if (route.kind === 'room') return <RoomGate roomId={route.roomId} />;
  if (route.kind === 'solo') {
    const script = publicScene(route.slug);
    if (script) return <SoloPractice slug={route.slug} script={script} />;
  }
  return <Landing />;
}

function RoomGate({ roomId }: { roomId: string }) {
  const [name, setName] = useState(loadName);
  const [draft, setDraft] = useState('');
  const [entered, setEntered] = useState(() => loadName().length > 0);

  // The static demo (GitHub Pages) has no server, so rooms can never
  // connect there — say so instead of spinning forever.
  if (import.meta.env.VITE_STATIC_DEMO) {
    return (
      <div className="landing">
        <div className="landing-card">
          <h1 className="logo">
            Serifu <span className="logo-jp">台詞</span>
          </h1>
          <p>
            <strong>This is the static demo</strong> — rooms (synced video, friends, voice chat)
            need the full Serifu server and don't run on this page.
          </p>
          <p className="muted">
            What works right here: solo memory practice with live speech scoring —
          </p>
          <div className="row">
            <a className="chip" href="#/p/meteor-promise">
              🎬 Episode 1: 流星群の約束
            </a>
            <a className="chip" href="#/p/iconic-scenes">
              名場面集 (full arc)
            </a>
          </div>
          <p className="fineprint">
            Room links work on the full deployment — ask the person who sent you this link for
            the app's real address.
          </p>
        </div>
      </div>
    );
  }

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
